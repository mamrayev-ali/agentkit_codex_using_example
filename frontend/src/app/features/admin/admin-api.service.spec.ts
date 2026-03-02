import { AdminApiError, AdminApiService } from './admin-api.service';

class FakeAuthService {
  accessToken(): string | null {
    return 'admin-token';
  }

  tenantId(): string | null {
    return 'acme';
  }
}

describe('AdminApiService', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads subject entitlements with bearer auth header', async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          tenant_id: 'acme',
          subject: 'user-123',
          enabled_modules: ['dashboard', 'watchlist'],
          audit_metadata: null,
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
          },
        },
      ),
    );
    vi.stubGlobal('fetch', fetchMock);

    const service = new AdminApiService(new FakeAuthService() as never);
    const result = await service.getEntitlements('user-123');

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/tenants/acme/entitlements/user-123',
      {
        method: 'GET',
        headers: {
          Authorization: 'Bearer admin-token',
        },
      },
    );
    expect(result.enabledModules).toEqual(['dashboard', 'watchlist']);
  });

  it('updates entitlements and returns audit metadata', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            tenant_id: 'acme',
            subject: 'user-123',
            enabled_modules: ['dashboard', 'dossiers'],
            audit_metadata: {
              event_id: 'evt-1',
              action: 'entitlements.updated',
              actor_subject: 'admin-1',
              target_subject: 'user-123',
              tenant_id: 'acme',
              occurred_at: '2026-03-02T12:00:00Z',
            },
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      ),
    );

    const service = new AdminApiService(new FakeAuthService() as never);
    const result = await service.updateEntitlements('user-123', ['dashboard', 'dossiers']);

    expect(result.auditMetadata?.eventId).toBe('evt-1');
    expect(result.enabledModules).toEqual(['dashboard', 'dossiers']);
  });

  it('loads tenant audit events', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(
          JSON.stringify({
            tenant_id: 'acme',
            events: [
              {
                event_id: 'evt-1',
                action: 'entitlements.updated',
                actor_subject: 'admin-1',
                target_subject: 'user-123',
                tenant_id: 'acme',
                outcome: 'success',
                occurred_at: '2026-03-02T12:00:00Z',
                reason: null,
              },
            ],
          }),
          {
            status: 200,
            headers: {
              'Content-Type': 'application/json',
            },
          },
        ),
      ),
    );

    const service = new AdminApiService(new FakeAuthService() as never);
    const result = await service.listAuditEvents();

    expect(result[0]?.action).toBe('entitlements.updated');
    expect(result[0]?.targetSubject).toBe('user-123');
  });

  it('surfaces backend 403 as AdminApiError', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'Forbidden' }), {
          status: 403,
          headers: {
            'Content-Type': 'application/json',
          },
        }),
      ),
    );

    const service = new AdminApiService(new FakeAuthService() as never);

    await expect(service.listAuditEvents()).rejects.toEqual(
      new AdminApiError('Forbidden', 403),
    );
  });
});
