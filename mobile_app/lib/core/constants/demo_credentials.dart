/// Demo account used for reviewers/testers to explore the app without
/// registering. Matches the account created by
/// `backend/scripts/seed_demo_user.py` — see that script and
/// `DEMO_CREDENTIALS.md` at the repo root for details and limitations
/// (the demo account currently lives in the API gateway's in-memory user
/// store, so it must be re-seeded after every `hermes_backend` restart).
class DemoCredentials {
  DemoCredentials._();

  static const String email = 'demo@hermeslingua.app';
  static const String username = 'demo_user';
  static const String password = 'HermesDemo#2026';
}
