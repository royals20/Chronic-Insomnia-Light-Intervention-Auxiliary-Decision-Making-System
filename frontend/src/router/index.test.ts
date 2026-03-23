import router from '@/router';
import { pinia } from '@/stores';
import { useAuthStore } from '@/stores/auth';


describe('router auth guard', () => {
  beforeEach(async () => {
    localStorage.clear();
    const authStore = useAuthStore(pinia);
    authStore.logout();
    await router.push('/login');
    await router.isReady();
  });

  it('redirects unauthenticated users to login', async () => {
    await router.push('/dashboard');

    expect(router.currentRoute.value.path).toBe('/login');
    expect(router.currentRoute.value.query.redirect).toBe('/dashboard');
  });

  it('redirects authenticated users away from login', async () => {
    const authStore = useAuthStore(pinia);
    authStore.token = 'demo-token';
    authStore.user = {
      id: 1,
      username: 'research_demo',
      full_name: '科研演示账号',
      role: 'researcher',
      is_active: true,
    };
    authStore.expiresAt = Date.now() + 60_000;
    authStore.initialized = true;
    localStorage.setItem('insomnia-demo-token', 'demo-token');
    localStorage.setItem('insomnia-demo-user', JSON.stringify(authStore.user));
    localStorage.setItem('insomnia-demo-expires-at', String(authStore.expiresAt));

    await router.push('/dashboard');
    await router.push('/login');

    expect(router.currentRoute.value.path).toBe('/dashboard');
  });

  it('redirects authenticated users without role access to forbidden', async () => {
    const authStore = useAuthStore(pinia);
    authStore.token = 'demo-token';
    authStore.user = {
      id: 2,
      username: 'data_entry_demo',
      full_name: '数据录入员',
      role: 'data_entry',
      is_active: true,
    };
    authStore.expiresAt = Date.now() + 60_000;
    authStore.initialized = true;

    await router.push('/recommendation-center');

    expect(router.currentRoute.value.path).toBe('/forbidden');
  });
});
