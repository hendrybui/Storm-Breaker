// Storm-Breaker Tauri shell (P9.3 + P9.4).
//
// - boots the bundled PyInstaller sidecar (onedir, shipped as a resource)
//   on startup and kills it on exit,
// - the main window points at the sidecar's http://127.0.0.1:2525,
// - closing the window hides to the system tray; tray menu: Show / Quit.
//
// Sidecar layout note (P9.2): the backend ships as an ONEDIR bundle
// (dist/storm-breaker-backend/, copied to resources/sidecar/) so the
// SQLite DB, check-c.json, secret_key.bin and capture dirs persist next
// to the app instead of a per-run temp extraction dir.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::sync::Mutex;

use tauri::{
    Manager, RunEvent,
    menu::{Menu, MenuItem},
    tray::TrayIconBuilder,
};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Handle to the running sidecar child, so we can stop it on exit (P9.3).
/// `Mutex<Option<_>>` because `CommandChild::kill` consumes ownership.
struct SidecarChild(Mutex<Option<CommandChild>>);

fn stop_sidecar(app: &tauri::AppHandle) {
    if let Some(state) = app.try_state::<SidecarChild>() {
        if let Some(child) = state.0.lock().expect("sidecar lock").take() {
            let _ = child.kill();
        }
    }
}

fn sidecar_exe(app: &tauri::AppHandle) -> std::path::PathBuf {
    let dir = app
        .path()
        .resource_dir()
        .expect("no resource dir")
        .join("sidecar/storm-breaker-backend");
    dir.join("storm-breaker-backend")
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // ---- P9.3: boot the backend sidecar --------------------------
            let exe = sidecar_exe(app.handle());
            let sidecar = app.shell().command(exe);
            let (mut rx, child) = sidecar
                .spawn()
                .expect("failed to start storm-breaker-backend sidecar");
            app.manage(SidecarChild(Mutex::new(Some(child))));

            // pipe sidecar stdout/stderr into this process' log
            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line)
                        | CommandEvent::Stderr(line) => {
                            println!(
                                "[sidecar] {}",
                                String::from_utf8_lossy(&line)
                            );
                        }
                        _ => {}
                    }
                }
            });

            // ---- P9.4: system tray (Show / Quit) --------------------------
            let show = MenuItem::with_id(app, "show", "Show", true, None::<&str>)?;
            let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&show, &quit])?;

            TrayIconBuilder::with_id("main-tray")
                .icon(app.default_window_icon().unwrap().clone())
                .tooltip("Storm-Breaker")
                .menu(&menu)
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "show" => {
                        if let Some(w) = app.get_webview_window("main") {
                            let _ = w.show();
                            let _ = w.set_focus();
                        }
                    }
                    "quit" => {
                        // stop the sidecar, then exit for real
                        stop_sidecar(app);
                        app.exit(0);
                    }
                    _ => {}
                })
                .build(app)?;

            Ok(())
        })
        .on_window_event(|window, event| {
            // P9.4: the [X] button hides to tray instead of quitting; use
            // the tray Quit to actually exit (stops the sidecar first).
            if let tauri::WindowEvent::CloseRequested { api, .. } = event {
                let _ = window.hide();
                api.prevent_close();
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app_handle, event| {
            if let RunEvent::Exit = event {
                // P9.3: make sure the sidecar never outlives the shell
                stop_sidecar(app_handle);
            }
        });
}
