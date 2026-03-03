import { NgIf } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { ActivatedRoute } from '@angular/router';

import { AuthService } from '../auth/auth.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [NgIf],
  template: `
    <section class="login-page">
      <div class="login-page__backdrop"></div>

      <div class="login-page__content">
        <div class="login-page__wordmark" aria-label="DECIDER">DECIDER</div>

        <article class="login-card card">
          <div class="login-card__body">
            <header class="login-card__header">
              <h1 class="login-card__title">Вход</h1>
            </header>

            <div *ngIf="errorMessage()" class="alert alert--danger">
              {{ errorMessage() }}
            </div>

            <form class="login-card__form u-stack" (submit)="onCorporateSignIn($event)">
              <label class="field">
                <span class="field__label">E-mail</span>
                <input
                  class="input login-card__input"
                  type="email"
                  name="email"
                  autocomplete="username"
                  placeholder="analyst@acme.decider.local"
                  [value]="email()"
                  (input)="onEmailInput($event)"
                />
              </label>

              <label class="field">
                <span class="field__label">Пароль</span>
                <span class="login-card__password-shell">
                  <input
                    class="input login-card__input login-card__input--password"
                    type="password"
                    autocomplete="current-password"
                    disabled
                    value="password"
                  />
                  <span class="login-card__password-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" focusable="false">
                      <path
                        d="M2.25 12s3.75-6 9.75-6 9.75 6 9.75 6-3.75 6-9.75 6-9.75-6-9.75-6Z"
                      />
                      <circle cx="12" cy="12" r="3.25" />
                    </svg>
                  </span>
                </span>
              </label>

              <button
                type="submit"
                class="btn btn--primary btn--lg login-card__cta"
                [disabled]="isSubmitting()"
              >
                {{ corporateButtonLabel() }}
              </button>
            </form>

          </div>

          <footer class="login-card__support">
            <p class="login-card__support-text">
              Новый пользователь? Регистрация недоступна. Доступ в Decider добавляется вручную.
            </p>
            <p class="login-card__support-text">
              Если возникли сложности с авторизацией, обратитесь в поддержку:
            </p>
            <p class="login-card__support-text">
              <a href="mailto:help@decider.invalid">help@decider.invalid</a>
              <span class="login-card__support-separator">или</span>
              <a href="tel:+79990001122">+7 (999) 000 11 22</a>
            </p>
          </footer>
        </article>
      </div>
    </section>
  `,
  styles: [
    `
      :host {
        display: block;
        min-height: 100vh;
      }

      .login-page {
        position: relative;
        min-height: 100vh;
        overflow: hidden;
        background: #dde1e5;
      }

      .login-page__backdrop {
        position: absolute;
        inset: 0;
        background: url('/auth/login-background.png') center / cover no-repeat;
      }

      .login-page__content {
        position: relative;
        z-index: 1;
        min-height: 100vh;
        display: grid;
        align-content: center;
        justify-items: center;
        gap: 28px;
        padding: clamp(var(--space-6), 6vw, 72px);
      }

      .login-page__wordmark {
        color: var(--neutral-950);
        font-size: clamp(38px, 4vw, 52px);
        font-weight: var(--font-weight-bold);
        letter-spacing: 0.12em;
        line-height: 1;
        text-transform: uppercase;
      }

      .login-card {
        width: min(100%, 572px);
        padding: 0;
        overflow: hidden;
        border-radius: 20px;
        border-color: color-mix(in srgb, var(--color-border) 82%, transparent);
        box-shadow: var(--shadow-lg);
        background: rgba(250, 250, 250, 0.96);
      }

      .login-card__body {
        padding: 34px 48px 30px;
      }

      .login-card__header {
        margin-bottom: 26px;
        text-align: center;
      }

      .login-card__title {
        margin: 0;
        font-size: clamp(28px, 2.3vw, 32px);
        line-height: var(--line-height-tight);
        font-weight: var(--font-weight-bold);
        color: var(--neutral-900);
      }

      .alert {
        margin-bottom: var(--space-4);
      }

      .login-card__form {
        gap: 18px;
      }

      .login-card__input {
        height: 48px;
        background: #dfe7f4;
        border-color: #c4ccd8;
        color: #1f2430;
      }

      .login-card__input[disabled] {
        opacity: 1;
        color: transparent;
        background: #dfe7f4;
        -webkit-text-security: disc;
      }

      .login-card__password-shell {
        position: relative;
        display: block;
      }

      .login-card__input--password {
        padding-right: 54px;
      }

      .login-card__password-icon {
        position: absolute;
        top: 1px;
        right: 1px;
        bottom: 1px;
        width: 48px;
        display: grid;
        place-items: center;
        border-left: 1px solid #c4ccd8;
        color: #4c525d;
        pointer-events: none;
      }

      .login-card__password-icon svg {
        width: 22px;
        height: 22px;
        fill: none;
        stroke: currentColor;
        stroke-width: 1.8;
      }

      .login-card__cta {
        width: 100%;
        margin-top: 6px;
        min-height: 54px;
      }

      .login-card__support {
        padding: 24px 40px 28px;
        border-top: 1px solid #d8dde7;
        background: #e6edf9;
        text-align: center;
      }

      .login-card__support-text {
        margin: 0;
        color: #6a7485;
        font-size: var(--font-size-xs);
        line-height: 1.45;
      }

      .login-card__support-text + .login-card__support-text {
        margin-top: 6px;
      }

      .login-card__support-separator {
        margin: 0 6px;
        color: #6a7485;
      }

      @media (max-width: 640px) {
        .login-page__content {
          padding: var(--space-4);
        }

        .login-page__wordmark {
          font-size: 28px;
          letter-spacing: 0.14em;
        }

        .login-card__body {
          padding: 28px 20px 24px;
        }

        .login-card__support {
          padding: 20px 20px 24px;
        }
      }
    `,
  ],
})
export class LoginPageComponent {
  private readonly authService = inject(AuthService);
  private readonly route = inject(ActivatedRoute);

  readonly email = signal('');
  readonly isSubmitting = signal(false);
  readonly errorMessage = signal('');

  corporateButtonLabel(): string {
    return this.isSubmitting() ? 'Перенаправляем…' : 'Войти';
  }

  onEmailInput(event: Event): void {
    const input = event.target as HTMLInputElement | null;
    this.email.set(input?.value ?? '');
  }

  async onCorporateSignIn(event: Event): Promise<void> {
    event.preventDefault();
    await this.beginLogin();
  }

  private async beginLogin(): Promise<void> {
    this.errorMessage.set('');
    this.isSubmitting.set(true);

    try {
      const redirectTo = this.route.snapshot.queryParamMap.get('redirectTo') ?? '/dashboard';
      const loginUrl = await this.authService.beginLogin(redirectTo, {
        loginHint: this.email().trim(),
      });
      window.location.assign(loginUrl);
    } catch {
      this.errorMessage.set('Не удалось начать вход. Повторите попытку.');
      this.isSubmitting.set(false);
    }
  }
}
