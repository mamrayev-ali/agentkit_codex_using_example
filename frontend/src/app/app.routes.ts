import type { Routes } from '@angular/router';

import { anonymousGuard } from './auth/anonymous.guard';
import { authGuard } from './auth/auth.guard';
import { moduleGuard } from './auth/module.guard';

export const appRoutes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    redirectTo: 'dashboard',
  },
  {
    path: 'login',
    canActivate: [anonymousGuard],
    loadComponent: () => import('./pages/login-page.component').then((m) => m.LoginPageComponent),
  },
  {
    path: 'auth/callback',
    canActivate: [anonymousGuard],
    loadComponent: () =>
      import('./pages/auth-callback-page.component').then((m) => m.AuthCallbackPageComponent),
  },
  {
    path: 'dashboard',
    canActivate: [authGuard, moduleGuard],
    data: {
      requiredModule: 'dashboard',
    },
    loadComponent: () =>
      import('./pages/dashboard-page.component').then((m) => m.DashboardPageComponent),
  },
  {
    path: 'dossiers',
    canActivate: [authGuard, moduleGuard],
    data: {
      requiredModule: 'dossiers',
    },
    loadComponent: () =>
      import('./pages/dossiers-page.component').then((m) => m.DossiersPageComponent),
  },
  {
    path: 'watchlist',
    canActivate: [authGuard, moduleGuard],
    data: {
      requiredModule: 'watchlist',
    },
    loadComponent: () =>
      import('./pages/watchlist-page.component').then((m) => m.WatchlistPageComponent),
  },
  {
    path: '**',
    canActivate: [authGuard],
    loadComponent: () =>
      import('./pages/not-found-page.component').then((m) => m.NotFoundPageComponent),
  },
];
