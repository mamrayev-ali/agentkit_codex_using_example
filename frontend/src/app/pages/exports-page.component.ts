import { NgIf } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../auth/auth.service';
import { WorkflowApiError, WorkflowApiService } from '../features/workflows/workflow-api.service';

@Component({
  selector: 'app-exports-page',
  standalone: true,
  imports: [NgIf, RouterLink],
  template: `
    <section class="page">
      <div class="u-between page-section">
        <div>
          <p class="badge badge--brand">Exports</p>
          <h2 class="page-title">Export request workflow</h2>
          <p class="u-muted">
            Request a tenant export and surface backend permission denials with explicit feedback.
          </p>
        </div>
        <div class="page-actions">
          <a class="btn btn--secondary" routerLink="/dashboard">Back to dashboard</a>
          <a class="btn btn--secondary" routerLink="/searches">Back to searches</a>
        </div>
      </div>

      <div class="stats-grid page-section">
        <article class="stat-card">
          <p class="stat-card__label">Dossiers</p>
          <div class="stat-card__value">{{ dossierCount() }}</div>
          <p class="u-muted">Records currently available for export scope review.</p>
        </article>

        <article class="stat-card">
          <p class="stat-card__label">Search requests</p>
          <div class="stat-card__value">{{ searchCount() }}</div>
          <p class="u-muted">Workflow requests that may feed export operations.</p>
        </article>

        <article class="stat-card">
          <p class="stat-card__label">Export scope</p>
          <div class="stat-card__value">
            {{ authService.hasScope('export:data') ? 'Present' : 'Missing' }}
          </div>
          <p class="u-muted">The backend still performs the final permission decision.</p>
        </article>

        <article class="stat-card">
          <p class="stat-card__label">Last result</p>
          <div class="stat-card__value">{{ exportStatusLabel() }}</div>
          <p class="u-muted">Tracks the most recent export request outcome in this UI session.</p>
        </article>
      </div>

      <div *ngIf="errorMessage()" class="alert alert--danger page-section">
        {{ errorMessage() }}
      </div>

      <div *ngIf="feedbackMessage()" class="alert alert--success page-section">
        {{ feedbackMessage() }}
      </div>

      <article class="panel u-stack">
        <div>
          <h3 class="section-title">Request tenant export</h3>
          <p class="u-muted">
            This calls the live tenant export endpoint. Missing scope or tenant mismatch is surfaced as explicit UI feedback.
          </p>
        </div>

        <div class="alert alert--info">
          {{
            authService.hasScope('export:data')
              ? 'Your current auth context includes export:data. The request should succeed if tenant state matches.'
              : 'Your current auth context does not include export:data. The request is expected to fail with a backend 403.'
          }}
        </div>

        <div class="form-actions">
          <button type="button" class="btn btn--primary" (click)="requestExport()" [disabled]="isSubmitting()">
            {{ isSubmitting() ? 'Requesting…' : 'Request export' }}
          </button>
        </div>
      </article>
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

      @media (max-width: 640px) {
        .page-actions,
        .form-actions {
          flex-direction: column;
        }
      }
    `,
  ],
})
export class ExportsPageComponent {
  readonly authService = inject(AuthService);

  private readonly workflowApi = inject(WorkflowApiService);

  readonly isSubmitting = signal(false);
  readonly errorMessage = signal('');
  readonly feedbackMessage = signal('');
  readonly exportStatusLabel = signal('Idle');
  readonly dossierCount = signal(0);
  readonly searchCount = signal(0);

  constructor() {
    void this.loadSummary();
  }

  async requestExport(): Promise<void> {
    this.isSubmitting.set(true);
    this.errorMessage.set('');
    this.feedbackMessage.set('');

    try {
      const result = await this.workflowApi.requestExport();
      this.exportStatusLabel.set('Accepted');
      this.feedbackMessage.set(`Export ${result.exportId} accepted for tenant ${result.tenantId}.`);
    } catch (error) {
      this.exportStatusLabel.set('Rejected');
      if (error instanceof WorkflowApiError && error.status === 403) {
        this.errorMessage.set(
          'Export request was rejected by the backend. The current session does not satisfy tenant or scope requirements.',
        );
      } else {
        this.errorMessage.set(error instanceof Error ? error.message : 'Unable to request export.');
      }
    } finally {
      this.isSubmitting.set(false);
    }
  }

  private async loadSummary(): Promise<void> {
    try {
      const [dossiers, searchRequests] = await Promise.all([
        this.workflowApi.listDossiers(),
        this.workflowApi.listSearchRequests(),
      ]);
      this.dossierCount.set(dossiers.length);
      this.searchCount.set(searchRequests.length);
    } catch {
      this.errorMessage.set('Unable to load export readiness data.');
    }
  }
}
