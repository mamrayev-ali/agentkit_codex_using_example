import { NgIf } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AuthService } from '../auth/auth.service';

function toSearchParams(route: ActivatedRoute): URLSearchParams {
  const params = new URLSearchParams();

  for (const key of route.snapshot.queryParamMap.keys) {
    const value = route.snapshot.queryParamMap.get(key);
    if (value !== null) {
      params.set(key, value);
    }
  }

  return params;
}

@Component({
  selector: 'app-auth-callback-page',
  standalone: true,
  imports: [NgIf, RouterLink],
  template: `
    <section class="auth-layout">
      <div class="auth-hero u-stack" style="gap: 1rem;">
        <p class="badge badge--info">Decider</p>
        <h1>Authorizing session</h1>
        <p class="u-text-muted">
          Validating OIDC callback and loading backend auth context.
        </p>
      </div>

      <div class="auth-card-wrap">
        <article class="auth-card card u-stack" style="gap: 1rem;">
          <h2 style="margin: 0;">{{ statusTitle() }}</h2>
          <p class="u-text-muted" style="margin: 0;">{{ statusDescription() }}</p>

          <div *ngIf="errorMessage()" class="alert alert--danger">
            {{ errorMessage() }}
          </div>

          <a *ngIf="errorMessage()" class="btn btn--secondary" routerLink="/login">
            Back to login
          </a>
        </article>
      </div>
    </section>
  `,
})
export class AuthCallbackPageComponent {
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly status = signal<'processing' | 'error'>('processing');
  readonly errorMessage = signal('');

  constructor() {
    void this.completeCallback();
  }

  statusTitle(): string {
    return this.status() === 'processing' ? 'Signing you in…' : 'Sign-in failed';
  }

  statusDescription(): string {
    return this.status() === 'processing'
      ? 'Please wait while we verify your tenant session.'
      : 'The callback could not be completed.';
  }

  private async completeCallback(): Promise<void> {
    const result = await this.authService.completeLoginFromCallback(toSearchParams(this.route));

    if (result.ok) {
      await this.router.navigateByUrl(result.redirectTo);
      return;
    }

    this.status.set('error');
    this.errorMessage.set(result.message);
  }
}
