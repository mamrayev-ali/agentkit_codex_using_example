import { NgIf } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { AuthService } from '../auth/auth.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [NgIf],
  template: `
    <section class="auth-layout">
      <div class="auth-hero u-stack" style="gap: 1rem;">
        <p class="badge badge--info">Decider</p>
        <h1>Secure tenant sign-in</h1>
        <p class="u-text-muted">
          Use your Keycloak account to access tenant-scoped modules.
        </p>
      </div>

      <div class="auth-card-wrap">
        <article class="auth-card card u-stack" style="gap: 1rem;">
          <h2 style="margin: 0;">Sign in</h2>
          <p class="u-text-muted" style="margin: 0;">
            Authentication uses Authorization Code + PKCE.
          </p>

          <div *ngIf="errorMessage()" class="alert alert--danger">
            {{ errorMessage() }}
          </div>

          <button
            type="button"
            class="btn btn--primary btn--lg"
            (click)="onSignIn()"
            [disabled]="isSubmitting()"
          >
            {{ isSubmitting() ? 'Redirecting…' : 'Sign in with Keycloak' }}
          </button>
        </article>
      </div>
    </section>
  `,
})
export class LoginPageComponent {
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);

  readonly isSubmitting = signal(false);
  readonly errorMessage = signal('');

  async onSignIn(): Promise<void> {
    this.errorMessage.set('');
    this.isSubmitting.set(true);

    try {
      const redirectTo = this.route.snapshot.queryParamMap.get('redirectTo') ?? '/dashboard';
      const loginUrl = await this.authService.beginLogin(redirectTo);
      window.location.assign(loginUrl);
    } catch {
      this.errorMessage.set('Unable to start login. Try again.');
      this.isSubmitting.set(false);
    }
  }
}
