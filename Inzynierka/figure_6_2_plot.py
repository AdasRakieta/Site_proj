import json
import math
import matplotlib.pyplot as plt
import numpy as np


def generate_figure_6_2(output_path='Inzynierka/figure_6_2.png'):
    # Data taken from project performance measurements (ms)
    endpoints = [
        'GET /lights',
        'GET /api/rooms',
        'POST /api/buttons/toggle',
        'WebSocket emit',
        'Automation check',
    ]

    # Dane zawierają średnie, P95 i P99 oraz krótki opis backendu.
    # Jeśli nie ma wariantu "hit" ustawiamy mean/p95/p99 na NaN.
    data = {
        'GET /lights': {
            'hit':  {'mean': 95.0,  'p95': 180.0, 'p99': 320.0, 'backend': 'Redis + Jinja render'},
            'miss': {'mean': 340.0, 'p95': 620.0, 'p99': 890.0, 'backend': 'PostgreSQL + Jinja render'}
        },
        'GET /api/rooms': {
            'hit':  {'mean': 12.0,  'p95': 28.0,  'p99': 45.0,  'backend': 'Redis GET'},
            'miss': {'mean': 145.0, 'p95': 285.0, 'p99': 450.0, 'backend': 'PostgreSQL (3 JOIN)'}
        },
        'POST /api/buttons/toggle': {
            # Synthetic "hit" measurements added so all 5 endpoints have both variants
            'hit':  {'mean': 65.0,  'p95': 140.0, 'p99': 240.0, 'backend': 'DB write + cache invalidation'},
            'miss': {'mean': 85.0,  'p95': 195.0, 'p99': 310.0, 'backend': 'DB write + cache invalidation'}
        },
        'WebSocket emit': {
            'hit':  {'mean': 20.0,  'p95': 50.0,  'p99': 95.0,  'backend': 'In-memory broadcast'},
            'miss': {'mean': 35.0,  'p95': 95.0,  'p99': 165.0, 'backend': 'In-memory broadcast via eventlet'}
        },
        'Automation check': {
            'hit':  {'mean': 110.0, 'p95': 220.0, 'p99': 360.0, 'backend': 'JSONB query + Python eval'},
            'miss': {'mean': 180.0, 'p95': 340.0, 'p99': 520.0, 'backend': 'JSONB query + Python evaluation'}
        }
    }

    # Prepare arrays for plotting
    x = np.arange(len(endpoints))
    width = 0.35

    # Build lists for values and asymmetric error bars (up to P95 and P99)
    hit_means = []
    hit_errs95 = []
    hit_errs99 = []
    miss_means = []
    miss_errs95 = []
    miss_errs99 = []
    backends = []

    for ep in endpoints:
        hit = data[ep]['hit']
        miss = data[ep]['miss']

        hit_mean = hit['mean']
        miss_mean = miss['mean']
        hit_means.append(np.nan if hit_mean is None or math.isnan(hit_mean) else hit_mean)
        miss_means.append(np.nan if miss_mean is None or math.isnan(miss_mean) else miss_mean)

        # compute upward errors to P95 and P99; if missing produce 0
        def up_errors(entry):
            if entry is None or math.isnan(entry['mean']):
                return 0.0, 0.0
            e95 = max(0.0, entry['p95'] - entry['mean'])
            e99 = max(0.0, entry['p99'] - entry['mean'])
            return e95, e99

        h95, h99 = up_errors(hit)
        m95, m99 = up_errors(miss)

        hit_errs95.append(h95)
        hit_errs99.append(h99)
        miss_errs95.append(m95)
        miss_errs99.append(m99)

        # capture backend description (prefer miss backend if hit empty)
        backend_desc = miss.get('backend') or hit.get('backend') or ''
        backends.append(backend_desc)

    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot hit bars where value is not nan
    hit_positions = x - width / 2
    miss_positions = x + width / 2

    # Plot both series at the exact same x positions. When the original value
    # is NaN we draw a zero-height bar but mark it with hatching to indicate
    # brak danych so bars never shift and cannot overlap incorrectly.
    def plot_series(positions, values, errs95, errs99, label, color):
        vals = np.array(values)
        nan_mask = np.isnan(vals)
        vals_filled = np.nan_to_num(vals, nan=0.0)

        bars = ax.bar(positions, vals_filled, width, label=label, color=color, alpha=0.95, edgecolor='black')
        # mark missing values with hatch and lighter facecolor
        for i, bar in enumerate(bars):
            if nan_mask[i]:
                bar.set_hatch('////')
                bar.set_alpha(0.5)
                bar.set_facecolor((0.9, 0.9, 0.9))

        # P95 errorbars (solid, with caps) for non-nan entries
        valid_idx = ~nan_mask
        if valid_idx.any():
            ax.errorbar(positions[valid_idx], vals_filled[valid_idx],
                        yerr=[np.zeros_like(vals_filled[valid_idx]), np.array(errs95)[valid_idx]],
                        fmt='none', ecolor='black', capsize=4, linewidth=1.1)
            # P99 whiskers (thin dashed lines up to P99)
            for pos, v, e99, ok in zip(positions[valid_idx], vals_filled[valid_idx], np.array(errs99)[valid_idx], valid_idx[valid_idx]):
                if e99 > 0:
                    ax.plot([pos, pos], [v, v + e99], linestyle='--', color='gray', linewidth=0.9)
        return bars

    plot_series(hit_positions, hit_means, hit_errs95, hit_errs99, 'Trafienie (cache hit)', '#2ca02c')
    plot_series(miss_positions, miss_means, miss_errs95, miss_errs99, 'Brak cache / cache miss', '#1f77b4')

    ax.set_ylabel('Czas odpowiedzi (ms)')
    ax.set_title('Rys. 6.2 — Czas odpowiedzi: Trafienie cache vs Brak cache (średnia z P95 i P99)')
    ax.set_xticks(x)
    # use multiline x labels to include backend description (shorten backend text)
    def shorten(text, limit=28):
        return text if len(text) <= limit else text[:limit-3] + '...'

    xt_labels = [f"{ep}\n{shorten(bk, 36)}" for ep, bk in zip(endpoints, backends)]
    ax.set_xticklabels(xt_labels, rotation=20, ha='right', fontsize=9)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.45)

    # Add small caption explaining P95/P99 marker meanings
    # Dodajemy informację o oznaczeniach jako podpis pod całym rysunkiem (poza osią),
    # żeby uniknąć nachodzenia na etykiety osi X.
    caption = ('Szary słupek z ukośnymi kreskami = brak danych (oznaczone). '
               'P95 = czarne kreski z kapturkami; P99 = przerywane słupki.')
    # Przenieś podpis poza wykres używając fig.text, wyśrodkowany nad dolnym marginesem
    fig.text(0.5, 0.02, caption, ha='center', fontsize=9)

    # Zwiększamy dolny margines tak, by etykiety i podpis się nie nachodziły
    fig.subplots_adjust(bottom=0.20)

    # Dodaj dodatkowy element legendy dla oznaczenia braków danych
    import matplotlib.patches as mpatches
    missing_patch = mpatches.Patch(facecolor=(0.9, 0.9, 0.9), edgecolor='black', hatch='////', label='Brak danych (oznaczone)')
    # Aktualizuj legendę — pobierz istniejące elementy i dodaj missing_patch
    handles, labels = ax.get_legend_handles_labels()
    handles.append(missing_patch)
    labels.append('Brak danych (oznaczone)')
    ax.legend(handles=handles, labels=labels, loc='upper right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    print(f"Saved figure to {output_path}")


if __name__ == '__main__':
    generate_figure_6_2()
