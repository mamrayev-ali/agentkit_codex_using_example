import { WorkflowApiService } from './workflow-api.service';

class FakeAuthService {
  accessToken(): string | null {
    return 'test-token';
  }

  tenantId(): string | null {
    return 'acme';
  }
}

describe('WorkflowApiService', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('loads tenant dossiers with bearer auth header', async () => {
    const fetchMock = vi.fn(async () =>
      new Response(
        JSON.stringify({
          tenant_id: 'acme',
          dossiers: [
            {
              tenant_id: 'acme',
              dossier_id: 'dos-1',
              subject_name: 'Acme LLP',
              subject_type: 'organization',
              created_at: '2026-03-02T10:00:00Z',
            },
          ],
        }),
        {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        },
      ),
    );
    vi.stubGlobal('fetch', fetchMock);

    const service = new WorkflowApiService(new FakeAuthService() as never);

    const dossiers = await service.listDossiers();

    expect(fetchMock).toHaveBeenCalledWith('http://localhost:8000/api/v1/tenants/acme/dossiers', {
      method: 'GET',
      headers: {
        Authorization: 'Bearer test-token',
      },
    });
    expect(dossiers[0]?.subjectName).toBe('Acme LLP');
  });

  it('maps export forbidden responses to WorkflowApiError with backend detail', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ detail: 'Forbidden' }), {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    );

    const service = new WorkflowApiService(new FakeAuthService() as never);

    await expect(service.requestExport()).rejects.toMatchObject({
      name: 'WorkflowApiError',
      message: 'Forbidden',
      status: 403,
    });
  });
});
