import { DatePipe, NgFor, NgIf } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { WorkflowApiService } from '../features/workflows/workflow-api.service';
import type { DossierRecord, SubjectType } from '../features/workflows/workflow.models';

@Component({
  selector: 'app-dossiers-page',
  standalone: true,
  imports: [NgIf, NgFor, FormsModule, RouterLink, DatePipe],
  template: `
    <section class="page">
      <div class="u-between page-section">
        <div>
          <p class="badge badge--brand">Dossiers</p>
          <h2 class="page-title">Tenant dossier workspace</h2>
          <p class="u-muted">
            Create organization and person records, then branch into search and export workflows.
          </p>
        </div>
        <div class="page-actions">
          <a class="btn btn--secondary" routerLink="/searches">Open searches</a>
          <a class="btn btn--secondary" routerLink="/exports">Open exports</a>
        </div>
      </div>

      <div *ngIf="feedbackMessage()" class="alert alert--success page-section">
        {{ feedbackMessage() }}
      </div>

      <div *ngIf="errorMessage()" class="alert alert--danger page-section">
        {{ errorMessage() }}
      </div>

      <div class="detail-layout page-section">
        <article class="panel u-stack">
          <div>
            <h3 class="section-title">Create dossier</h3>
            <p class="u-muted">
              Use this form to seed a new organization or person record for the tenant.
            </p>
          </div>

          <form class="u-stack" (ngSubmit)="createDossier()">
            <label class="field">
              <span class="field__label">Subject name</span>
              <input
                class="input"
                type="text"
                name="subjectName"
                [(ngModel)]="subjectName"
                placeholder="Acme LLP"
              />
              <span class="field__hint">
                Use the real entity name that the search pipeline should reference.
              </span>
            </label>

            <label class="field">
              <span class="field__label">Subject type</span>
              <select class="select" name="subjectType" [(ngModel)]="subjectType">
                <option value="organization">Organization</option>
                <option value="person">Person</option>
              </select>
              <span class="field__hint">
                The backend validates this value against the public API contract.
              </span>
            </label>

            <div class="form-actions">
              <button type="submit" class="btn btn--primary" [disabled]="isSaving()">
                {{ isSaving() ? 'Creating…' : 'Create dossier' }}
              </button>
            </div>
          </form>
        </article>

        <article class="panel u-stack">
          <div>
            <h3 class="section-title">Selected dossier</h3>
            <p class="u-muted">Current review context for follow-up search actions.</p>
          </div>

          <div *ngIf="selectedDossier(); else noSelection" class="detail-hero u-stack">
            <div>
              <span class="badge badge--info">{{ selectedDossier()?.subjectType }}</span>
            </div>
            <div>
              <h3 class="section-title">{{ selectedDossier()?.subjectName }}</h3>
              <p class="u-muted">{{ selectedDossier()?.dossierId }}</p>
            </div>
            <div class="detail-meta">
              <p class="u-muted">Created {{ selectedDossier()?.createdAt | date: 'medium' }}</p>
            </div>
            <div class="page-actions">
              <a
                class="btn btn--secondary"
                routerLink="/searches"
                [queryParams]="{ dossierId: selectedDossier()?.dossierId }"
              >
                Launch search
              </a>
            </div>
          </div>

          <ng-template #noSelection>
            <div class="empty-state">
              <h3>No dossier selected</h3>
              <p class="u-muted">
                Choose a dossier from the table below to inspect it and launch a search.
              </p>
            </div>
          </ng-template>
        </article>
      </div>

      <div *ngIf="isLoading(); else dossierTable" class="panel">
        <div class="skeleton list-loading"></div>
      </div>

      <ng-template #dossierTable>
        <div *ngIf="dossiers().length === 0" class="empty-state">
          <h3>No dossiers yet</h3>
          <p class="u-muted">Create the first dossier to unlock search and export workflows.</p>
        </div>

        <div *ngIf="dossiers().length > 0" class="table-wrap">
          <table class="table table--zebra">
            <thead>
              <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Created</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr
                *ngFor="let dossier of dossiers()"
                [class.is-selected]="dossier.dossierId === selectedDossierId()"
              >
                <td>
                  <strong>{{ dossier.subjectName }}</strong>
                  <div class="u-muted">{{ dossier.dossierId }}</div>
                </td>
                <td>{{ dossier.subjectType }}</td>
                <td>{{ dossier.createdAt | date: 'medium' }}</td>
                <td>
                  <div class="table-actions">
                    <button
                      type="button"
                      class="btn btn--ghost btn--sm"
                      (click)="selectDossier(dossier.dossierId)"
                    >
                      Details
                    </button>
                    <a
                      class="btn btn--ghost btn--sm"
                      routerLink="/searches"
                      [queryParams]="{ dossierId: dossier.dossierId }"
                    >
                      Search
                    </a>
                  </div>
                </td>
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
      .table-actions,
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
        .table-actions,
        .form-actions {
          flex-direction: column;
        }
      }
    `,
  ],
})
export class DossiersPageComponent {
  private readonly workflowApi = inject(WorkflowApiService);

  readonly isLoading = signal(true);
  readonly isSaving = signal(false);
  readonly errorMessage = signal('');
  readonly feedbackMessage = signal('');
  readonly dossiers = signal<DossierRecord[]>([]);
  readonly selectedDossierId = signal<string | null>(null);
  readonly selectedDossier = computed(
    () => this.dossiers().find((item) => item.dossierId === this.selectedDossierId()) ?? null,
  );

  subjectName = '';
  subjectType: SubjectType = 'organization';

  constructor() {
    void this.loadDossiers();
  }

  selectDossier(dossierId: string): void {
    this.selectedDossierId.set(dossierId);
  }

  async createDossier(): Promise<void> {
    const subjectName = this.subjectName.trim();
    if (!subjectName) {
      this.errorMessage.set('Subject name is required.');
      return;
    }

    this.isSaving.set(true);
    this.errorMessage.set('');
    this.feedbackMessage.set('');

    try {
      const dossier = await this.workflowApi.createDossier({
        subjectName,
        subjectType: this.subjectType,
      });
      this.dossiers.set([dossier, ...this.dossiers()]);
      this.selectedDossierId.set(dossier.dossierId);
      this.subjectName = '';
      this.subjectType = 'organization';
      this.feedbackMessage.set(`Dossier ${dossier.subjectName} was created.`);
    } catch (error) {
      this.errorMessage.set(error instanceof Error ? error.message : 'Unable to create dossier.');
    } finally {
      this.isSaving.set(false);
    }
  }

  private async loadDossiers(): Promise<void> {
    this.isLoading.set(true);
    this.errorMessage.set('');

    try {
      const dossiers = await this.workflowApi.listDossiers();
      this.dossiers.set(dossiers);
      this.selectedDossierId.set(dossiers[0]?.dossierId ?? null);
    } catch {
      this.errorMessage.set('Unable to load dossiers for this tenant.');
    } finally {
      this.isLoading.set(false);
    }
  }
}
