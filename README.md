# CTRL-NEXT HEMS

Custom Home Assistant integration for controlling the CTRL-NEXT HEMS battery setup through Home Assistant.

This repository is a proof of concept for personal use only.

## HACS installation

1. Install HACS in Home Assistant if you have not already.
2. Make sure this repository is public on GitHub.
3. In HACS, add this repository as a custom repository of type Integration.
4. Install the integration from HACS.
5. Restart Home Assistant and add the integration from the UI.

## Updates

This repository is prepared for HACS updates through GitHub releases. When you want to publish a new version:

1. Update the version in [manifest.json](manifest.json).
2. Create and push a tag such as `v0.1.1`.
3. The release workflow will publish a GitHub release for that tag.
4. Home Assistant will then show the HACS update button for the new release.

## Repository layout

The integration files live in the repository root, so HACS is configured with `content_in_root: true`.