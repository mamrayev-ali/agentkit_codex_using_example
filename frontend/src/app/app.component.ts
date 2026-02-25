import { NgIf } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { environment } from '../environments/environment';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, NgIf],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  readonly appName = 'Decider';
  readonly environmentName = environment.name;

  private moduleEntitlements: string[] = ['dashboard', 'dossiers', 'watchlist'];

  applyAuthContext(authContext: { module_entitlements?: unknown }): void {
    const nextModules = this.normalizeModuleEntitlements(authContext.module_entitlements);
    this.moduleEntitlements = nextModules.length > 0 ? nextModules : ['dashboard'];
  }

  isModuleVisible(moduleKey: string): boolean {
    return this.moduleEntitlements.includes(moduleKey);
  }

  private normalizeModuleEntitlements(value: unknown): string[] {
    if (!Array.isArray(value)) {
      return [];
    }

    const normalized: string[] = [];
    for (const moduleKey of value) {
      if (typeof moduleKey !== 'string') {
        continue;
      }

      const trimmed = moduleKey.trim().toLowerCase();
      if (!trimmed || normalized.includes(trimmed)) {
        continue;
      }

      normalized.push(trimmed);
    }

    return normalized;
  }
}
