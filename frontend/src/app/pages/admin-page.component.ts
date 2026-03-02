import { DatePipe, NgClass, NgFor, NgIf } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { AuthService } from '../auth/auth.service';
import { AdminApiError, AdminApiService } from '../features/admin/admin-api.service';
import type {
  AuditEventRecord,
  SubjectEntitlements,
  SupportedModule,
} from '../features/admin/admin.models';

const _AVAILABLE_MODULES: Array<{ key: SupportedModule; label: string; hint: string }> = [
  {
    key: 'dashboard',
    label: 'Dashboard',
    hint: 'Baseline shell access and tenant overview.',
  },
  {
    key: 'dossiers',
    label: 'Dossiers',
    hint: 'Dossiers, searches, and exports workspace access.',
  },
  {
    key: 'watchlist',
    label: 'Watchlist',
    hint: 'Monitored entities and watchlist workflows.',
  },
];

@Component({
  selector: 'app-admin-page',
  standalone: true,
  imports: [NgIf, NgFor, NgClass, FormsModule, DatePipe],
  template: `
    <section class="page">
      <div class="u-between page-section">
        <div>
          <p class="badge badge--brand">Admin</p>
          <h2 class="page-title">Entitlements and audit control</h2>
          <p class="u-muted">
            Manage tenant subject module access and review the latest export and permission audit trail.
          </p>
        </div>
        <div class="page-actions">
          <button type="button" class="btn btn--secondary" (click)="reloadAuditEvents()" [disabled]="isAuditLoading()">
            {{ isAuditLoading() ? 'Refreshing…' : 'Refresh audit' }}
          </button>
          <button
            type="button"
            class="btn btn--primary"
            (click)="refreshCurrentAuthContext()"
            [disabled]="isContextRefreshing()"
          >
            {{ isContextRefreshing() ? 'Refreshing…' : 'Refresh auth context' }}
          </button>
        </div>
      </div>

      <div *ngIf="feedbackMessage()" class="alert alert--success page-section">
        {{ feedbackMessage() }}
      </div>

      <div *ngIf="errorMessage()" class="alert alert--danger page-section">
        {{ errorMessage() }}
      </div>

      <div class="stats-grid page-section">
        <article class="stat-card">
          <p class="stat-card__label">Current subject</p>
          <div class="stat-card__value">{{ authService.subject() ?? 'Unknown' }}</div>
          <p class="u-muted">Admin shell access is derived from current backend roles/scopes.</p>
        </article>
        <article class="stat-card">
          <p class="stat-card__label">Tenant</p>
          <div class="stat-card__value">{{ authService.tenantId() ?? 'Unknown' }}</div>
          <p class="u-muted">All admin reads and writes stay inside the active tenant path.</p>
        </article>
        <article class="stat-card">
          <p class="stat-card__label">Audit events</p>
          <div class="stat-card__value">{{ auditEvents().length }}</div>
          <p class="u-muted">Most recent events returned by the backend admin audit API.</p>
        </article>
      </div>

      <div class="detail-layout page-section">
        <article class="panel u-stack">
          <div>
            <h3 class="section-title">Subject entitlements</h3>
            <p class="u-muted">
              Load any tenant subject, toggle allowed modules, then persist changes through the admin endpoint.
            </p>
          </div>

          <form class="u-stack" (ngSubmit)="loadSubjectEntitlements()">
            <label class="field">
              <span class="field__label">Subject</span>
              <input
                class="input"
                type="text"
                name="subject"
                [(ngModel)]="subjectValue"
                placeholder="user-123"
              />
              <span class="field__hint">Use the backend subject identifier from the active tenant.</span>
            </label>

            <div class="form-actions">
              <button type="submit" class="btn btn--secondary" [disabled]="isSubjectLoading()">
                {{ isSubjectLoading() ? 'Loading…' : 'Load entitlements' }}
              </button>
            </div>
          </form>

          <div *ngIf="loadedEntitlements() as entitlements; else noEntitlements" class="u-stack">
            <div class="detail-hero u-stack">
              <div>
                <span class="badge badge--info">Subject</span>
              </div>
              <div>
                <h3 class="section-title">{{ entitlements.subject }}</h3>
                <p class="u-muted">Tenant {{ entitlements.tenantId }}</p>
              </div>
            </div>

            <div class="u-stack">
              <label *ngFor="let module of availableModules" class="module-option">
                <input
                  type="checkbox"
                  [checked]="selectedModules().includes(module.key)"
                  (change)="toggleModule(module.key, $any($event.target).checked)"
                />
                <span>
                  <strong>{{ module.label }}</strong>
                  <span class="field__hint">{{ module.hint }}</span>
                </span>
              </label>
            </div>

            <div class="form-actions">
              <button type="button" class="btn btn--primary" (click)="saveEntitlements()" [disabled]="isSaving()">
                {{ isSaving() ? 'Saving…' : 'Save entitlements' }}
              </button>
            </div>
          </div>

          <ng-template #noEntitlements>
            <div class="empty-state">
              <h3>No subject loaded</h3>
              <p class="u-muted">Load a tenant subject before editing module access.</p>
            </div>
          </ng-template>
        </article>

        <article class="panel u-stack">
          <div class="panel__header">
            <div>
              <h3 class="section-title">Audit trail</h3>
              <p class="u-muted">Recent tenant admin actions and export requests.</p>
            </div>
            <span class="badge badge--info">{{ auditEvents().length }} events</span>
          </div>

          <div *ngIf="isAuditLoading()" class="skeleton audit-loading"></div>

          <div *ngIf="!isAuditLoading() && auditEvents().length === 0" class="empty-state">
            <h3>No audit events yet</h3>
            <p class="u-muted">Once permission updates or exports happen, they will appear here.</p>
          </div>

          <div *ngIf="!isAuditLoading() && auditEvents().length > 0" class="u-stack">
            <article *ngFor="let event of auditEvents()" class="card audit-card">
              <div class="u-between audit-card__topline">
                <div>
                  <strong>{{ actionLabel(event) }}</strong>
                  <p class="u-muted">
                    {{ event.actorSubject }}
                    <span *ngIf="event.targetSubject">→ {{ event.targetSubject }}</span>
                  </p>
                </div>
                <span [ngClass]="outcomeBadgeClass(event)">{{ event.outcome }}</span>
              </div>
              <p class="u-muted">
                {{ event.occurredAt | date: 'medium' }} · {{ event.tenantId }}
                <span *ngIf="event.reason">· {{ event.reason }}</span>
              </p>
            </article>
          </div>
        </article>
      </div>
    </section>
  `,
  styles: [
    `
      .page-title {
        margin: var(--space-3) 0 var(--space-2);
      }

      .page-actions,
      .form-actions {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-3);
      }

      .form-actions {
        justify-content: flex-end;
      }

      .module-option {
        display: grid;
        grid-template-columns: auto 1fr;
        gap: var(--space-3);
        align-items: start;
        padding: var(--space-3);
        border: 1px solid var(--color-border);
        border-radius: var(--radius-md);
      }

      .audit-card {
        padding: var(--space-4);
      }

      .audit-card__topline {
        gap: var(--space-4);
        align-items: start;
      }

      .audit-loading {
        min-height: 280px;
      }

      @media (max-width: 640px) {
        .page-actions,
        .form-actions {
          flex-direction: column;
        }
      }
    `,
  ],
})
export class AdminPageComponent {
  readonly authService = inject(AuthService);

  private readonly adminApi = inject(AdminApiService);

  readonly availableModules = _AVAILABLE_MODULES;
  readonly errorMessage = signal('');
  readonly feedbackMessage = signal('');
  readonly isSubjectLoading = signal(false);
  readonly isSaving = signal(false);
  readonly isAuditLoading = signal(true);
  readonly isContextRefreshing = signal(false);
  readonly loadedEntitlements = signal<SubjectEntitlements | null>(null);
  readonly selectedModules = signal<SupportedModule[]>([]);
  readonly auditEvents = signal<AuditEventRecord[]>([]);

  subjectValue = '';

  constructor() {
    this.subjectValue = this.authService.subject() ?? '';
    void this.reloadAuditEvents();
  }

  async loadSubjectEntitlements(): Promise<void> {
    const subject = this.subjectValue.trim();
    if (!subject) {
      this.errorMessage.set('Enter a subject before loading entitlements.');
      return;
    }

    this.isSubjectLoading.set(true);
    this.errorMessage.set('');
    this.feedbackMessage.set('');

    try {
      const result = await this.adminApi.getEntitlements(subject);
      this.loadedEntitlements.set(result);
      this.selectedModules.set([...result.enabledModules]);
    } catch (error) {
      this.errorMessage.set(error instanceof Error ? error.message : 'Unable to load entitlements.');
    } finally {
      this.isSubjectLoading.set(false);
    }
  }

  toggleModule(moduleKey: SupportedModule, isEnabled: boolean): void {
    if (isEnabled) {
      if (!this.selectedModules().includes(moduleKey)) {
        this.selectedModules.set([...this.selectedModules(), moduleKey]);
      }
      return;
    }

    this.selectedModules.set(this.selectedModules().filter((item) => item !== moduleKey));
  }

  async saveEntitlements(): Promise<void> {
    const entitlements = this.loadedEntitlements();
    if (entitlements === null) {
      this.errorMessage.set('Load a subject before saving entitlements.');
      return;
    }

    this.isSaving.set(true);
    this.errorMessage.set('');
    this.feedbackMessage.set('');

    try {
      const result = await this.adminApi.updateEntitlements(
        entitlements.subject,
        [...this.selectedModules()],
      );
      this.loadedEntitlements.set(result);
      this.selectedModules.set([...result.enabledModules]);
      await this.reloadAuditEvents();

      if (result.subject === this.authService.subject()) {
        const refreshed = await this.refreshCurrentAuthContext();
        this.feedbackMessage.set(
          refreshed
            ? `Entitlements updated for ${result.subject}. Current auth context was refreshed.`
            : `Entitlements updated for ${result.subject}. Refresh the current session to pick up the new auth context.`,
        );
      } else {
        this.feedbackMessage.set(
          `Entitlements updated for ${result.subject}. The subject will see changes after the next auth-context refresh.`,
        );
      }
    } catch (error) {
      if (error instanceof AdminApiError && error.status === 403) {
        this.errorMessage.set(
          'Admin update was rejected by the backend. The current session is not authorized for this tenant action.',
        );
      } else {
        this.errorMessage.set(error instanceof Error ? error.message : 'Unable to update entitlements.');
      }
    } finally {
      this.isSaving.set(false);
    }
  }

  async reloadAuditEvents(): Promise<void> {
    this.isAuditLoading.set(true);
    this.errorMessage.set('');

    try {
      const events = await this.adminApi.listAuditEvents();
      this.auditEvents.set(events);
    } catch (error) {
      if (error instanceof AdminApiError && error.status === 403) {
        this.errorMessage.set(
          'Audit access was rejected by the backend. The current session is not authorized for tenant audit review.',
        );
      } else {
        this.errorMessage.set(error instanceof Error ? error.message : 'Unable to load tenant audit events.');
      }
    } finally {
      this.isAuditLoading.set(false);
    }
  }

  async refreshCurrentAuthContext(): Promise<boolean> {
    this.isContextRefreshing.set(true);
    this.errorMessage.set('');

    try {
      const authContext = await this.authService.refreshAuthContext();
      if (authContext === null) {
        this.errorMessage.set('Current session could not be refreshed from backend auth context.');
        return false;
      }
      return true;
    } catch {
      this.errorMessage.set('Unable to refresh the current auth context.');
      return false;
    } finally {
      this.isContextRefreshing.set(false);
    }
  }

  actionLabel(event: AuditEventRecord): string {
    return event.action === 'entitlements.updated' ? 'Entitlements updated' : 'Export requested';
  }

  outcomeBadgeClass(event: AuditEventRecord): string {
    return event.outcome === 'success' ? 'badge badge--success' : 'badge badge--danger';
  }
}
