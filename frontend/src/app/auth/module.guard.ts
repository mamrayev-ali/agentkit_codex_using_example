import { inject } from '@angular/core';
import { type CanActivateFn, Router } from '@angular/router';

import { AuthService } from './auth.service';

export const moduleGuard: CanActivateFn = async (route) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const requiredModuleValue = route.data?.['requiredModule'];
  const requiredModule =
    typeof requiredModuleValue === 'string' ? requiredModuleValue.trim().toLowerCase() : '';

  if (!requiredModule) {
    return true;
  }

  const isAuthenticated = await authService.ensureAuthenticated();
  if (!isAuthenticated) {
    return router.createUrlTree(['/login']);
  }

  if (authService.hasModule(requiredModule)) {
    return true;
  }

  return router.createUrlTree(['/dashboard']);
};
