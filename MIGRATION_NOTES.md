# Migration Notes — Odoo 15.0

## Status

**Code-migrated only. NOT install-verified on a live Odoo 15.0 server.**

These modules were originally developed and tested on **Odoo 19.0**. The code
on this branch has been adapted for Odoo 15.0 via static analysis and known
API changes, but has **not** been installed and exercised on a running Odoo 15.0
instance.

## What was adapted

- All view XML: `<list>` view type replaced with `<tree>` (Odoo 15 does not support `<list>`)
- All view XML: inline Python expressions (`invisible="state == 'x'"`) converted to
  `attrs={}` domain syntax (`attrs="{'invisible': [('state', '=', 'x')]}"`)
  — Odoo 15 does not support inline Python-style expressions in view attributes
- `haboo_facebook_instagram_messenger` and `haboo_facebook_instagram_integration`:
  `discuss.channel` → `mail.channel` (renamed in Odoo 16.0)
  `discuss.channel.member` → `mail.channel.partner` (renamed in Odoo 16.0)
  View inherit ref `mail.discuss_channel_view_form` → `mail.view_channel_form`
- `haboo_facebook_instagram_messenger/models/messenger_template.py`:
  `render_engine="qweb"` removed from `fields.Html` (parameter not available until Odoo 16.0)
- Manifest versions: updated from 19.0.x.x.x to 15.0.x.x.x
- Dead (unregistered) JS and XML files removed from all static/src/ directories

## Known risks / not yet verified at runtime

- Scheduler (ir.cron) action binding may need manual re-configuration after install
- Access rights (ir.model.access) are unchanged — verify they match your 15.0 security model
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

- [ ] Install each module on a clean Odoo 15.0 database
- [ ] Confirm no import errors in the Odoo log
- [ ] Open the form views for each model and verify visibility rules work
- [ ] Trigger at least one webhook / API call per integration
- [ ] Check scheduled actions are listed in Settings → Technical → Automation
