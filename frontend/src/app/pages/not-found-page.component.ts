import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-not-found-page',
  standalone: true,
  imports: [RouterLink],
  template: `
    <section class="page">
      <h2>Not Found</h2>
      <p>This route is not available in the shell yet.</p>
      <a routerLink="/dashboard">Back to dashboard</a>
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
      a {
        color: #0f172a;
      }
    `,
  ],
})
export class NotFoundPageComponent {}
