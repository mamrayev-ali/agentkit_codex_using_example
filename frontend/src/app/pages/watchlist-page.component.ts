import { Component } from '@angular/core';

@Component({
  selector: 'app-watchlist-page',
  standalone: true,
  template: `
    <section class="page">
      <h2>Watchlist</h2>
      <p>Route skeleton for monitored entities and alert states.</p>
    </section>
  `,
  styles: [
    `
      .page {
        background: rgba(255, 255, 255, 0.75);
        border: 1px solid rgba(15, 23, 42, 0.12);
        border-radius: 16px;
        padding: 1rem 1.25rem;
      }
      h2 {
        margin-top: 0;
      }
    `,
  ],
})
export class WatchlistPageComponent {}
