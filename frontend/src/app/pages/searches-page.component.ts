import { DatePipe, NgFor, NgIf } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { WorkflowApiService } from '../features/workflows/workflow-api.service';
import type {
  DossierRecord,
  SearchRequestRecord,
  SearchRequestStatus,
} from '../features/workflows/workflow.models';

@Component({
  selector: 'app-searches-page',
  standalone: true,
  imports: [NgIf, NgFor, FormsModule, RouterLink, DatePipe],
  template: `
    <section class="page">
      <div class="u-between page-section">
        <div>
          <p class="badge badge--brand">Searches</p>
          <h2 class="page-title">Search request workflow</h2>
          <p class="u-muted">
            Launch tenant-scoped searches against existing dossiers and track current request status.
          </p>
        </div>
        <div class="page-actions">
          <a class="btn btn--secondary" routerLink="/dossiers">Open dossiers</a>
          <button type="button" class="btn btn--secondary" (click)="refreshStatuses()" [disabled]="isRefreshing()">
            {{ isRefreshing() ? 'Refreshing…' : 'Refresh statuses' }}
          </button>
        </div>
      </div>

      <div *ngIf="feedbackMessage()" class="alert alert--success page-section">
        {{ feedbackMessage() }}
      </div>

      <div *ngIf="errorMessage()" class="alert alert--danger page-section">
        {{ errorMessage() }}
      </div>

      <div *ngIf="isLoading(); else searchContent" class="panel">
        <div class="skeleton list-loading"></div>
      </div>

      <ng-template #searchContent>
        <div *ngIf="dossiers().length === 0" class="empty-state">
          <h3>No dossiers available</h3>
          <p class="u-muted">Create a dossier first. Search requests require a valid dossier ID.</p>
          <a class="btn btn--primary" routerLink="/dossiers">Create dossier</a>
        </div>

        <div *ngIf="dossiers().length > 0" class="detail-layout page-section">
          <article class="panel u-stack">
            <div>
              <h3 class="section-title">Launch search</h3>
              <p class="u-muted">Submit a backend search request for the selected tenant dossier.</p>
            </div>

            <form class="u-stack" (ngSubmit)="createSearchRequest()">
              <label class="field">
                <span class="field__label">Dossier</span>
                <select class="select" name="dossierId" [(ngModel)]="selectedDossierIdValue">
                  <option *ngFor="let dossier of dossiers()" [value]="dossier.dossierId">
                    {{ dossier.subjectName }} · {{ dossier.subjectType }}
                  </option>
                </select>
                <span class="field__hint">The request will be stored under the selected dossier.</span>
              </label>

              <label class="field">
                <span class="field__label">Query text</span>
                <input
                  class="input"
                  type="text"
                  name="queryText"
                  [(ngModel)]="queryText"
                  placeholder="open sanctions check"
                />
                <span class="field__hint">Describe the check the ingestion pipeline should perform.</span>
              </label>

              <label class="field">
                <span class="field__label">Source key</span>
                <input
                  class="input"
                  type="text"
                  name="sourceKey"
                  [(ngModel)]="sourceKey"
                  placeholder="gov-registry"
                />
                <span class="field__hint">Must match the source identifier expected by the backend workflow.</span>
              </label>

              <label class="field">
                <span class="field__label">Remote URL</span>
                <input
                  class="input"
                  type="url"
                  name="remoteUrl"
                  [(ngModel)]="remoteUrl"
                  placeholder="https://example.com/api/company"
                />
                <span class="field__hint">The backend applies SSRF-safe validation before queueing the request.</span>
              </label>

              <div class="form-actions">
                <button type="submit" class="btn btn--primary" [disabled]="isSubmitting()">
                  {{ isSubmitting() ? 'Submitting…' : 'Submit search request' }}
                </button>
              </div>
            </form>
          </article>

          <article class="panel u-stack">
            <div>
              <h3 class="section-title">Current dossier</h3>
              <p class="u-muted">Searches will be associated with the selected dossier.</p>
            </div>

            <div *ngIf="selectedDossier(); else noSelection" class="detail-hero u-stack">
              <div>
                <span class="badge badge--info">{{ selectedDossier()?.subjectType }}</span>
              </div>
              <div>
                <h3 class="section-title">{{ selectedDossier()?.subjectName }}</h3>
                <p class="u-muted">{{ selectedDossier()?.dossierId }}</p>
              </div>
            </div>

            <ng-template #noSelection>
              <div class="empty-state">
                <h3>No dossier selected</h3>
                <p class="u-muted">Choose a dossier before sending a search request.</p>
              </div>
            </ng-template>
          </article>
        </div>

        <div *ngIf="searchRequests().length === 0" class="empty-state">
          <h3>No search requests yet</h3>
          <p class="u-muted">Submit the first request to start building the tenant activity feed.</p>
        </div>

        <div *ngIf="searchRequests().length > 0" class="table-wrap">
          <table class="table table--zebra">
            <thead>
              <tr>
                <th>Query</th>
                <th>Dossier</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let search of searchRequests()">
                <td>
                  <strong>{{ search.queryText }}</strong>
                  <div class="u-muted">{{ search.requestId }}</div>
                </td>
                <td>{{ dossierName(search.dossierId) }}</td>
                <td><span [class]="statusBadgeClass(search.status)">{{ search.status }}</span></td>
                <td>{{ search.createdAt | date: 'medium' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </ng-template>
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

      .list-loading {
        min-height: 240px;
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
export class SearchesPageComponent {
  private readonly workflowApi = inject(WorkflowApiService);
  private readonly route = inject(ActivatedRoute);

  readonly isLoading = signal(true);
  readonly isSubmitting = signal(false);
  readonly isRefreshing = signal(false);
  readonly errorMessage = signal('');
  readonly feedbackMessage = signal('');
  readonly dossiers = signal<DossierRecord[]>([]);
  readonly searchRequests = signal<SearchRequestRecord[]>([]);

  selectedDossierIdValue = '';
  queryText = '';
  sourceKey = 'gov-registry';
  remoteUrl = 'https://example.com/api/company';

  constructor() {
    void this.load();
  }

  selectedDossier(): DossierRecord | null {
    return this.dossiers().find((item) => item.dossierId === this.selectedDossierIdValue) ?? null;
  }

  dossierName(dossierId: string): string {
    return this.dossiers().find((item) => item.dossierId === dossierId)?.subjectName ?? dossierId;
  }

  statusBadgeClass(status: SearchRequestStatus): string {
    switch (status) {
      case 'completed':
        return 'badge badge--success';
      case 'failed':
        return 'badge badge--danger';
      case 'running':
        return 'badge badge--info';
      default:
        return 'badge badge--warning';
    }
  }

  async refreshStatuses(): Promise<void> {
    this.isRefreshing.set(true);
    this.errorMessage.set('');

    try {
      const searchRequests = await this.workflowApi.listSearchRequests();
      this.searchRequests.set(searchRequests);
    } catch {
      this.errorMessage.set('Unable to refresh search statuses.');
    } finally {
      this.isRefreshing.set(false);
    }
  }

  async createSearchRequest(): Promise<void> {
    if (!this.selectedDossierIdValue.trim()) {
      this.errorMessage.set('Select a dossier before submitting a search request.');
      return;
    }

    this.isSubmitting.set(true);
    this.errorMessage.set('');
    this.feedbackMessage.set('');

    try {
      const result = await this.workflowApi.createSearchRequest({
        dossierId: this.selectedDossierIdValue,
        queryText: this.queryText.trim(),
        sourceKey: this.sourceKey.trim(),
        remoteUrl: this.remoteUrl.trim(),
      });

      this.searchRequests.set([result.searchRequest, ...this.searchRequests()]);
      this.queryText = '';
      this.feedbackMessage.set(
        `Search request ${result.searchRequest.requestId} queued with task ${result.enqueueMetadata.taskId}.`,
      );
    } catch (error) {
      this.errorMessage.set(
        error instanceof Error ? error.message : 'Unable to submit the search request.',
      );
    } finally {
      this.isSubmitting.set(false);
    }
  }

  private async load(): Promise<void> {
    this.isLoading.set(true);
    this.errorMessage.set('');

    try {
      const [dossiers, searchRequests] = await Promise.all([
        this.workflowApi.listDossiers(),
        this.workflowApi.listSearchRequests(),
      ]);
      this.dossiers.set(dossiers);
      this.searchRequests.set(searchRequests);

      const requestedDossierId = this.route.snapshot.queryParamMap.get('dossierId');
      this.selectedDossierIdValue =
        (requestedDossierId !== null &&
        dossiers.some((item) => item.dossierId === requestedDossierId)
          ? requestedDossierId
          : dossiers[0]?.dossierId) ?? '';
    } catch {
      this.errorMessage.set('Unable to load search workflow data.');
    } finally {
      this.isLoading.set(false);
    }
  }
}
