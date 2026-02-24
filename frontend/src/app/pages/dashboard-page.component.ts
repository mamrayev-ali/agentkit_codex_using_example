import { Component } from '@angular/core';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  template: `
    <section class="page">
      <h2>Dashboard</h2>
      <p>Shell route for tenant summary and quick operational signals.</p>
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
export class DashboardPageComponent {}
