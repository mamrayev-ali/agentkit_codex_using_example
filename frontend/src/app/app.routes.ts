import type { Routes } from '@angular/router';

export const appRoutes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'dashboard',
  },
  {
    path: 'dashboard',
    loadComponent: () =>
      import('./pages/dashboard-page.component').then((m) => m.DashboardPageComponent),
  },
  {
    path: 'dossiers',
    loadComponent: () =>
      import('./pages/dossiers-page.component').then((m) => m.DossiersPageComponent),
  },
  {
    path: 'watchlist',
    loadComponent: () =>
      import('./pages/watchlist-page.component').then((m) => m.WatchlistPageComponent),
  },
  {
    path: '**',
    loadComponent: () =>
      import('./pages/not-found-page.component').then((m) => m.NotFoundPageComponent),
  },
];
