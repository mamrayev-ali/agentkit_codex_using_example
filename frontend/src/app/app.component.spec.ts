import '@angular/compiler';
import { AppComponent } from './app.component';

describe('AppComponent', () => {
  it('exposes shell title and environment label', () => {
    const app = new AppComponent();

    expect(app.appName).toBe('Decider');
    expect(app.environmentName).toBe('development');
  });

  it('shows all module links by default', () => {
    const app = new AppComponent();

    expect(app.isModuleVisible('dashboard')).toBe(true);
    expect(app.isModuleVisible('dossiers')).toBe(true);
    expect(app.isModuleVisible('watchlist')).toBe(true);
  });

  it('applies backend module entitlements to visibility logic', () => {
    const app = new AppComponent();

    app.applyAuthContext({
      module_entitlements: ['dashboard', 'watchlist', 'watchlist'],
    });

    expect(app.isModuleVisible('dashboard')).toBe(true);
    expect(app.isModuleVisible('watchlist')).toBe(true);
    expect(app.isModuleVisible('dossiers')).toBe(false);
  });

  it('falls back to dashboard when backend entitlements are missing', () => {
    const app = new AppComponent();

    app.applyAuthContext({ module_entitlements: null });

    expect(app.isModuleVisible('dashboard')).toBe(true);
    expect(app.isModuleVisible('watchlist')).toBe(false);
  });
});
