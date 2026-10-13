# Deploy ResearchLens on Render

1. Connect Render to a GitHub repository containing these project files.
2. In Render select **New > Blueprint** and select that repository. `render.yaml` defines the service.
3. Configure `OPENAI_API_KEY` and `OPENALEX_API_KEY` as environment secrets in Render (do not commit them). OPENAI_API_KEY enables AI analysis.
4. Wait for the deployment to report Live, then open the assigned `onrender.com` URL.

Important: On a free ephemeral instance, the local SQLite `papers.db` is not persistent across redeploys/restarts. Use a managed database or persistent disk before relying on saved papers. Free instance availability and cold-start behavior depend on Render's current plan policy. This is an MVP, not an authenticated multi-user production service. Do not upload sensitive or unpublished papers to a public deployment without adding access controls and a privacy review. The app currently also offers entering API keys in the sidebar; for a public deployment, prefer server-side environment secrets and restrict access to the app before sharing it.
