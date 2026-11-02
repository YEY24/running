import '../dashboard/index.css';
import './style.css';
import { useMemo, useState } from 'react';
import type { Activity } from '@/types';
import {
  getActivityData,
  getAvailableYears,
  parseMovingTime,
} from '@/hooks/useActivities';
import { useTheme } from '@/hooks/useTheme';
import { ContributionHeatmap } from '@/components/ContributionHeatmap';
import { ActivityLog } from '@/components/ActivityLog';
import { RouteMap } from '@/components/RouteMap';
import { CalendarWidget } from '@/components/CalendarWidget';
import sync from '@/static/sync-status.json';

const km = (meters: number) =>
  (meters / 1000).toLocaleString('en', { maximumFractionDigits: 1 });

export default function EuanDashboard() {
  const activities = getActivityData() as Activity[];
  const { dark, toggle } = useTheme();
  const [year, setYear] = useState<number | null>(null);
  const [selected, setSelected] = useState<Activity | null>(null);
  const years = useMemo(() => getAvailableYears(activities), [activities]);
  const filtered = activities.filter(
    (a) => year === null || Number(a.start_date_local.slice(0, 4)) === year
  );
  const distance = filtered.reduce((n, a) => n + a.distance, 0);
  const seconds = filtered.reduce(
    (n, a) => n + parseMovingTime(a.moving_time),
    0
  );
  const longest = filtered.reduce((n, a) => Math.max(n, a.distance), 0);
  const routeCount = filtered.filter((a) => a.summary_polyline).length;
  const weeks = useMemo(() => {
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    now.setDate(now.getDate() - ((now.getDay() + 6) % 7));
    return Array.from({ length: 12 }, (_, i) => {
      const start = new Date(now);
      start.setDate(start.getDate() - (11 - i) * 7);
      const end = new Date(start);
      end.setDate(end.getDate() + 7);
      return {
        label: start.toLocaleDateString('en-GB', {
          day: 'numeric',
          month: 'short',
        }),
        distance: activities
          .filter((a) => {
            const d = new Date(a.start_date_local);
            return d >= start && d < end;
          })
          .reduce((s, a) => s + a.distance / 1000, 0),
      };
    });
  }, [activities]);
  const maxWeek = Math.max(1, ...weeks.map((w) => w.distance));

  return (
    <div className="dashboard euan min-h-screen bg-[var(--color-bg)]">
      <header className="euan-header">
        <a href="#" className="brand">
          <span className="brand-mark">e.</span> EUAN / RUNNING
        </a>
        <nav aria-label="Main navigation">
          <a href="#history">History</a>
          <a href="#routes">Routes</a>
          <a
            href="https://github.com/YEY24/running"
            target="_blank"
            rel="noreferrer"
          >
            GitHub ↗
          </a>
          <button
            onClick={toggle}
            aria-label={`Switch to ${dark ? 'light' : 'dark'} theme`}
          >
            {dark ? '☀ Light' : '☾ Dark'}
          </button>
        </nav>
      </header>
      <main className="euan-main">
        <section className="euan-hero">
          <div>
            <p className="eyebrow">THE RUNNING JOURNAL · EUAN</p>
            <h1>
              One run.
              <br />
              <em>Then another.</em>
            </h1>
            <p className="hero-copy">
              A personal record of the miles, the places, and the days that add
              up.
            </p>
            <div className="source-line">
              <span
                className={
                  sync.synced_at ? 'status-dot connected' : 'status-dot'
                }
              />
              {sync.synced_at
                ? `Updated ${new Date(sync.synced_at).toLocaleString('en-GB', { timeZone: 'Europe/Berlin' })} · Berlin time`
                : 'Waiting for the first Intervals.icu sync'}
            </div>
          </div>
          <div className="hero-art" aria-hidden="true">
            <svg viewBox="0 0 400 260">
              <path d="M50 210 C20 120 170 235 150 120 S300 20 340 80 S210 220 260 240" />
              <path
                className="route-shadow"
                d="M50 210 C20 120 170 235 150 120 S300 20 340 80 S210 220 260 240"
              />
              <circle cx="50" cy="210" r="7" />
              <circle cx="260" cy="240" r="7" />
            </svg>
            <span>KEEP SHOWING UP</span>
          </div>
        </section>
        <div className="section-bar">
          <h2>The miles, so far</h2>
          <label>
            Period{' '}
            <select
              aria-label="Statistics year"
              value={year ?? 'all'}
              onChange={(e) => {
                setYear(
                  e.target.value === 'all' ? null : Number(e.target.value)
                );
                setSelected(null);
              }}
            >
              <option value="all">All time</option>
              {years.map((y) => (
                <option key={y}>{y}</option>
              ))}
            </select>
          </label>
        </div>
        <section className="metric-grid" aria-label="Running statistics">
          {[
            ['Distance', km(distance), 'km covered'],
            ['Runs', filtered.length.toLocaleString(), 'times out the door'],
            ['Time running', (seconds / 3600).toFixed(1), 'hours moving'],
            ['Longest run', km(longest), 'km in one go'],
          ].map(([label, value, unit]) => (
            <article className="metric" key={label}>
              <p>{label}</p>
              <strong>{value}</strong>
              <span>{unit}</span>
            </article>
          ))}
        </section>
        {!activities.length && (
          <section className="empty-state">
            <span className="eyebrow">A FRESH START</span>
            <h2>Your first run belongs here.</h2>
            <p>
              Once Intervals.icu is connected, your real running history will
              appear automatically. No sample activities are shown.
            </p>
          </section>
        )}
        <div className="content-grid">
          <div className="main-column">
            <section className="weekly-card">
              <div className="section-bar">
                <h2>A little, often.</h2>
                <span>Last 12 weeks · km</span>
              </div>
              <div
                className="week-chart"
                role="img"
                aria-label={weeks
                  .map((w) => `${w.label}: ${w.distance.toFixed(1)} km`)
                  .join('; ')}
              >
                {weeks.map((w, i) => (
                  <div key={w.label} className="week-column">
                    <span>{w.distance ? w.distance.toFixed(0) : ''}</span>
                    <div
                      className={i === 11 ? 'week-bar current' : 'week-bar'}
                      style={{
                        height: `${Math.max(2, (w.distance / maxWeek) * 120)}px`,
                      }}
                      title={`${w.label}: ${w.distance.toFixed(1)} km`}
                    />
                    <small>{i % 3 === 0 || i === 11 ? w.label : ''}</small>
                  </div>
                ))}
              </div>
            </section>
            <ContributionHeatmap
              activities={activities}
              year={year ?? years[0] ?? new Date().getFullYear()}
              filter="Run"
              onSelectActivity={setSelected}
            />
            <section id="history">
              <ActivityLog
                activities={filtered}
                years={years}
                year={year}
                setYear={(y) => {
                  setYear(y);
                  setSelected(null);
                }}
                selectedActivity={selected}
                onSelectActivity={setSelected}
                filter="Run"
              />
            </section>
          </div>
          <aside className="side-column">
            <section id="routes">
              <div className="section-bar">
                <h2>Places on foot</h2>
                <span>{routeCount} routes</span>
              </div>
              <RouteMap
                activities={filtered}
                allActivities={activities}
                selectedActivity={selected}
                dark={dark}
                onClearSelection={() => setSelected(null)}
              />
            </section>
            <CalendarWidget
              activities={filtered}
              selectedActivity={selected}
              onSelectActivity={setSelected}
            />
            <section className="note-card">
              <span className="eyebrow">THE EVERYDAY PRACTICE</span>
              <p>Progress lives in the ordinary days.</p>
              <span>
                Recorded on Apple Watch.
                <br />
                Synced through Intervals.icu.
              </span>
            </section>
          </aside>
        </div>
      </main>
      <footer className="euan-footer">
        <span>EUAN / RUNNING · {new Date().getFullYear()}</span>
        <span>
          Built on{' '}
          <a href="https://github.com/yihong0618/running_page">running_page</a>{' '}
          · Maps © CARTO © OpenStreetMap
        </span>
      </footer>
    </div>
  );
}
