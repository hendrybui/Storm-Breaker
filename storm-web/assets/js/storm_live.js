/* storm_live.js — realtime push consumer (P10) + live ops view (P11).
 *
 * Replaces the panel's fixed-interval blind polling for the new surface:
 * one SSE connection carries beacon/listener/strike events; /api/live gives
 * the initial snapshot. The legacy poll endpoints are untouched.
 */
(function () {
    'use strict';

    var MAX_ROWS = 60;
    var source = null;

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    }

    function row(kind, text, at) {
        var colours = { beacon: 'text-blue-400', listener: 'text-emerald-400', strike: 'text-amber-400' };
        return '<div class="flex gap-2 py-1 border-b border-slate-800 text-[11px] font-mono">' +
            '<span class="' + (colours[kind] || 'text-slate-400') + ' w-16 shrink-0">' + esc(kind) + '</span>' +
            '<span class="text-slate-300 flex-1 break-all">' + esc(text) + '</span>' +
            '<span class="text-slate-600 shrink-0">' + esc((at || '').slice(11, 19)) + '</span>' +
            '</div>';
    }

    function describe(kind, e) {
        if (kind === 'beacon') return e.uid + ' beacon (' + e.expected_ms + 'ms)';
        if (kind === 'listener') return e.peer + ':' + e.peer_port + ' -> ' + e.host + ':' + e.port;
        if (kind === 'strike') return e.payload_type + ' -> ' + e.target + ' | callback=' + (e.callback_ok ? 'VERIFIED' : 'NO');
        return JSON.stringify(e);
    }

    function push(kind, e) {
        var feed = document.getElementById('live-feed');
        if (!feed) return;
        var empty = feed.querySelector('.live-empty');
        if (empty) empty.remove();
        feed.insertAdjacentHTML('afterbegin', row(kind, describe(kind, e), e.at));
        while (feed.children.length > MAX_ROWS) feed.removeChild(feed.lastChild);
    }

    function renderSnapshot(data) {
        var ls = document.getElementById('live-listeners');
        if (ls) {
            ls.innerHTML = (data.listeners || []).map(function (l) {
                return '<div class="text-[11px] font-mono text-slate-300">' + esc(l.name) + ' :' + l.port +
                    ' <span class="text-emerald-400">' + l.connections + ' conn</span></div>';
            }).join('') || '<div class="text-[11px] text-slate-600">no listeners</div>';
        }
        var bs = document.getElementById('live-beacons');
        if (bs) {
            bs.innerHTML = (data.beacons || []).map(function (b) {
                return '<div class="text-[11px] font-mono text-slate-300">' + esc(b.uid) +
                    ' <span class="text-blue-400">' + b.count + ' beacons</span>' +
                    (b.interval_ms ? ' <span class="text-slate-500">~' + b.interval_ms + 'ms</span>' : '') +
                    (b.missed ? ' <span class="text-red-400">' + b.missed + ' missed</span>' : '') + '</div>';
            }).join('') || '<div class="text-[11px] text-slate-600">no beacons observed</div>';
        }
        var sub = document.getElementById('live-subscribers');
        if (sub) sub.textContent = data.subscribers;
    }

    function snapshot() {
        $.get('/api/live', function (data) {
            renderSnapshot(data);
            var feed = document.getElementById('live-feed');
            if (feed && !feed.children.length) {
                (data.events || []).slice().reverse().forEach(function (e) { push(e.kind, e); });
            }
        });
    }

    function connect() {
        if (source) source.close();
        source = new EventSource('/api/events');
        ['beacon', 'listener', 'strike'].forEach(function (kind) {
            source.addEventListener(kind, function (msg) {
                var e = JSON.parse(msg.data);
                push(kind, e);
                snapshot();
            });
        });
        var status = document.getElementById('live-status');
        if (status) status.textContent = 'live';
        source.onerror = function () {
            var s = document.getElementById('live-status');
            if (s) s.textContent = 'reconnecting';
        };
    }

    window.StormLive = {
        start: function () {
            if (!document.getElementById('live-feed')) return;
            snapshot();
            connect();
            if (window._liveTimer) clearInterval(window._liveTimer);
            window._liveTimer = setInterval(snapshot, 10000);  // slow reconcile
        }
    };

    document.addEventListener('DOMContentLoaded', function () {
        if (document.getElementById('live-feed')) window.StormLive.start();
    });
})();
