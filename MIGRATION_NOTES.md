# Migration Notes — Odoo 17.0

## Status

**Code-migrated only. NOT install-verified on a live Odoo 17.0 server.**

These modules were originally developed and tested on **Odoo 19.0**. The code
on this branch has been adapted for Odoo 17.0 via static analysis and known
API changes, but has **not** been installed and exercised on a running Odoo 17.0
instance.

## What was adapted

- Manifest versions: updated from 19.0.x.x.x to 17.0.x.x.x
- View XML syntax is unchanged: same `<list>` and inline `invisible=` syntax as 16.0
- Python ORM API is unchanged from 16.0 for the APIs used by these modules
- Dead (unregistered) JS and XML files removed from all static/src/ directories

## Known risks / not yet verified at runtime

- Scheduler (ir.cron) action binding may need manual re-configuration after install
- Access rights (ir.model.access) are unchanged — verify they match your 17.0 security model
- No UI regression testing was performed
- External API integrations (Shopify, Gupshup, Tata, etc.) behave the same, but
  any dependency on a specific Odoo internal (mail thread, discuss, etc.) may surface
  only at runtime

## Modules included

- `haboo_lime_chat`
- `haboo_gupshup_integration`
- `haboo_qikberry`
- `haboo_google_place_api`
- `haboo_tata_whatsapp_integration`
- `haboo_tata_smartflo`
- `haboo_facebook_instagram_messenger`
- `haboo_facebook_instagram_integration`
- `haboo_shopify_integration`
- `haboo_wondersoft_integration`

## Test checklist before going live

- [ ] Install each module on a clean Odoo 17.0 database
- [ ] Confirm no import errors in the Odoo log
- [ ] Open the form views for each model and verify visibility rules work
- [ ] Trigger at least one webhook / API call per integration
- [ ] Check scheduled actions are listed in Settings → Technical → Automation
