import { NgIf } from '@angular/common';
import { Inject, Component } from '@angular/core';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { environment } from '../environments/environment';
import { AuthService } from './auth/auth.service';

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

  constructor(@Inject(AuthService) private readonly authService: AuthService) {}

  authContext() {
    return this.authService.authContext();
  }

  isAuthenticated(): boolean {
    return this.authService.isAuthenticated();
  }

  isModuleVisible(moduleKey: string): boolean {
    return this.authService.hasModule(moduleKey);
  }

  logout(): void {
    const logoutUrl = this.authService.createLogoutUrl();
    this.authService.clearSession();
    window.location.assign(logoutUrl);
  }
}
