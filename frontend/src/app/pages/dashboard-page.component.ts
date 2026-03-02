import { DatePipe, NgFor, NgIf } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthService } from '../auth/auth.service';
import { WorkflowApiService } from '../features/workflows/workflow-api.service';
import type { DossierRecord, SearchRequestRecord } from '../features/workflows/workflow.models';

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [NgIf, NgFor, RouterLink, DatePipe],
  template: `
    <section class="page">
      <div class="u-between page-section">
        <div>
          <p class="badge badge--brand">Dashboard</p>
          <h2 class="page-title">Tenant workflow overview</h2>
          <p class="u-muted">
            Track dossier volume, recent search activity, and export readiness from one place.
          </p>
        </div>

        <div class="dashboard-actions">
          <a class="btn btn--secondary" routerLink="/dossiers">Open dossiers</a>
          <a class="btn btn--secondary" routerLink="/searches">Run search</a>
          <a class="btn btn--primary" routerLink="/exports">Open exports</a>
        </div>
      </div>

      <div *ngIf="errorMessage()" class="alert alert--danger page-section">
        {{ errorMessage() }}
      </div>

      <div *ngIf="isLoading(); else dashboardContent" class="stats-grid page-section">
        <div class="stat-card skeleton stat-card--loading"></div>
        <div class="stat-card skeleton stat-card--loading"></div>
        <div class="stat-card skeleton stat-card--loading"></div>
        <div class="stat-card skeleton stat-card--loading"></div>
      </div>

      <ng-template #dashboardContent>
        <div class="stats-grid page-section">
          <article class="stat-card">
            <p class="stat-card__label">Dossiers</p>
            <div class="stat-card__value">{{ dossiers().length }}</div>
            <p class="u-muted">Active tenant records ready for review.</p>
          </article>

          <article class="stat-card">
            <p class="stat-card__label">Search requests</p>
            <div class="stat-card__value">{{ searchRequests().length }}</div>
            <p class="u-muted">Queued and completed checks in the workflow.</p>
          </article>

          <article class="stat-card">
            <p class="stat-card__label">Completed searches</p>
            <div class="stat-card__value">{{ completedSearchCount() }}</div>
            <p class="u-muted">Ready-to-review results already finished.</p>
          </article>

          <article class="stat-card">
            <p class="stat-card__label">Export access</p>
            <div class="stat-card__value">{{ canExport() ? 'Ready' : 'Blocked' }}</div>
            <p class="u-muted">
              {{
                canExport()
                  ? 'Scope available for export requests.'
                  : 'Backend will reject export requests without scope.'
              }}
            </p>
          </article>
        </div>

        <div class="grid-cards page-section">
          <article class="chart-card dashboard-card">
            <div class="panel__header">
              <div>
                <h3 class="section-title">Recent search activity</h3>
                <p class="u-muted">Latest requests returned by the tenant workflow API.</p>
              </div>
              <a class="btn btn--ghost btn--sm" routerLink="/searches">View all</a>
            </div>

            <div *ngIf="recentSearches().length === 0" class="empty-state">
              <h3>No search requests yet</h3>
              <p class="u-muted">
                Create a dossier first, then launch the first search from the search workspace.
              </p>
            </div>

            <div *ngIf="recentSearches().length > 0" class="u-stack">
              <article *ngFor="let search of recentSearches()" class="card dashboard-activity">
                <div class="u-between">
                  <div>
                    <strong>{{ search.queryText }}</strong>
                    <p class="u-muted">{{ search.requestId }} · {{ search.createdAt | date: 'medium' }}</p>
                  </div>
                  <span [class]="statusBadgeClass(search.status)">{{ search.status }}</span>
                </div>
              </article>
            </div>
          </article>

          <article class="chart-card dashboard-card">
            <div class="panel__header">
              <div>
                <h3 class="section-title">Recent dossiers</h3>
                <p class="u-muted">Most recent tenant dossiers available for search and export flows.</p>
              </div>
              <a class="btn btn--ghost btn--sm" routerLink="/dossiers">Manage</a>
            </div>

            <div *ngIf="recentDossiers().length === 0" class="empty-state">
              <h3>No dossiers yet</h3>
              <p class="u-muted">
                Use the dossier workspace to create the first person or organization record.
              </p>
            </div>

            <div *ngIf="recentDossiers().length > 0" class="u-stack">
              <article *ngFor="let dossier of recentDossiers()" class="card dashboard-activity">
                <div class="u-between">
                  <div>
                    <strong>{{ dossier.subjectName }}</strong>
                    <p class="u-muted">{{ dossier.subjectType }} · {{ dossier.createdAt | date: 'medium' }}</p>
                  </div>
                  <a
                    class="btn btn--ghost btn--sm"
                    routerLink="/searches"
                    [queryParams]="{ dossierId: dossier.dossierId }"
                  >
                    Search
                  </a>
                </div>
              </article>
            </div>
          </article>
        </div>
      </ng-template>
    </section>
  `,
  styles: [
    `
      .page-title {
        margin: var(--space-3) 0 var(--space-2);
      }

      .dashboard-actions {
        display: flex;
        flex-wrap: wrap;
        gap: var(--space-3);
      }

      .dashboard-card {
        min-height: 100%;
      }

      .dashboard-activity {
        padding: var(--space-4);
      }

      .stat-card--loading {
        min-height: 172px;
      }

      @media (max-width: 640px) {
        .dashboard-actions {
          width: 100%;
          flex-direction: column;
        }
      }
    `,
  ],
})
export class DashboardPageComponent {
  private readonly workflowApi = inject(WorkflowApiService);
  private readonly authService = inject(AuthService);

  readonly isLoading = signal(true);
  readonly errorMessage = signal('');
  readonly dossiers = signal<DossierRecord[]>([]);
  readonly searchRequests = signal<SearchRequestRecord[]>([]);
  readonly completedSearchCount = computed(
    () => this.searchRequests().filter((item) => item.status === 'completed').length,
  );
  readonly recentDossiers = computed(() => this.dossiers().slice(0, 5));
  readonly recentSearches = computed(() => this.searchRequests().slice(0, 5));

  constructor() {
    void this.load();
  }

  canExport(): boolean {
    return this.authService.hasScope('export:data');
  }

  statusBadgeClass(status: SearchRequestRecord['status']): string {
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
    } catch {
      this.errorMessage.set('Unable to load dashboard workflow data.');
    } finally {
      this.isLoading.set(false);
    }
  }
}
