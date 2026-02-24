import '@angular/compiler';
import { AppComponent } from './app.component';

describe('AppComponent', () => {
  it('exposes shell title and environment label', () => {
    const app = new AppComponent();

    expect(app.appName).toBe('Decider');
    expect(app.environmentName).toBe('development');
  });
});
