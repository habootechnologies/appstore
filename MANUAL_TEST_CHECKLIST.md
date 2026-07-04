# Manual Test Checklist — haboo_qr_code downgrade branches

Static analysis (py_compile + lxml XML parse + node --check) has passed on both 16.0
and 15.0 branches. The items below **cannot be verified without a running Odoo instance**
and must all pass before marking either branch Active in the App Store.

Items marked **[UNVERIFIED - needs manual check]** are cases where the migration involved
genuine API uncertainty that only a real install can resolve.

---

## Branch: 16.0

### Install / module load

- [ ] `pip install qrcode[pil]` is available in the Odoo 16 virtualenv (same dependency as 17)
- [ ] Module installs without errors: `python odoo-bin -d testdb -i haboo_qr_code`
- [ ] No `ir.ui.view` XML load errors in the server log during install
- [ ] All XML record IDs resolve correctly:
  - `haboo_qr_code.scan_product_qrcode` (client action)
  - `haboo_qr_code.product_qr_code_view_form`
  - `haboo_qr_code.product_qr_code_view_tree`
  - `haboo_qr_code.product_qr_code_action`
  - `haboo_qr_code.menu_product_qr_code_root`
  - `haboo_qr_code.menu_product_qr_code`
  - `haboo_qr_code.action_report_product_qr_code`
  - `haboo_qr_code.paperformat_product_qr_code_report`
  - `haboo_qr_code.sequence_product_qr_name`
  - `haboo_qr_code.sequence_product_qr_code`
- [ ] No duplicate `action_report_product_qr_code` record error (the report XML defines this
      id twice; Odoo should treat the second as an update, but verify no install-time warning)

### Views and menus

- [ ] "Product QR" top-level menu appears in the app switcher
- [ ] The menu icon renders (note: `web_icon` references `product_qr_code` but the module
      folder is `haboo_qr_code` — this is a pre-existing bug; verify whether icon loads or
      falls back to a generic icon)
- [ ] List/tree view of `product.qr.code` opens and shows columns: ID, Product, In Date, Out Date
- [ ] Form view opens for a new record

### Dynamic visibility (`attrs` domain syntax)

This is the core change in 16.0. Each button's visibility must be tested:

- [ ] In **Draft** state: only "Generate QR" button is visible
- [ ] In **QR** state: "Print QR" and "IN" buttons visible; "Generate QR" hidden
- [ ] In **In** state: "Scan Product QR Code" button visible; others hidden
- [ ] In **Scanned** state: "OUT" button visible
- [ ] In **Out** state: no action buttons visible; `product_id` field is readonly
- [ ] `product_id` field is **editable** in Draft/QR/In states
- [ ] `product_id` field is **readonly** when state = 'out'

### Record creation and QR generation

- [ ] Creating a new record auto-assigns `product_name` from sequence (format: `QRxxxxxx`)
- [ ] Creating a new record auto-assigns `id_record` from sequence (format: `QR/YYYY/xxxxx`)
- [ ] `qr_code_image` binary is populated after create (check in the DB or via technical menu)
- [ ] `file_name` is populated after create

### PDF report

- [ ] Clicking "Print QR" from a record in QR state triggers the PDF download
- [ ] The PDF renders at 50mm × 50mm with the QR code image visible
- [ ] `web.basic_layout` renders without layout errors (header/footer present or absent
      as expected for a minimal label-style report)
- [ ] `o.qr_code_image.decode('utf-8')` does not raise AttributeError in the QWeb template
      context (binary field returns bytes in Odoo 16; if it returns a str, remove `.decode()`)

### QR scanner client action

- [ ] The "Scan Product QR Code" button (visible in 'in' state) opens the scanner widget
- [ ] The QR scanner UI renders in the browser (camera permission prompt appears)
- [ ] Javascript assets load without 404: verify in browser Network tab:
  - `haboo_qr_code/static/src/js/product_qr_code_scan.js`  
    ⚠ manifest references path as `product_qr_code/...` — if 404, the module name
    in the `assets` dict must be changed from `product_qr_code` to `haboo_qr_code`
  - `haboo_qr_code/static/src/js/html5-qrcode.js`
  - `haboo_qr_code/static/src/xml/product_qr_code_template.xml`
- [ ] No JS console errors on scanner page load
- [ ] Scanning a valid QR code calls `mark_as_scanned` and reloads
- [ ] Scanning an invalid QR code shows "Invalid!" message
- [ ] Scanning an already-scanned code shows "QR code Already Scanned."

### State transitions end-to-end

- [ ] Draft → Generate QR → QR (state = 'qr')
- [ ] QR → IN (state = 'in', in_date populated)
- [ ] In → Scan → Scanned (state = 'scanned' via `mark_as_scanned`)
- [ ] Scanned → OUT (state = 'out', out_date populated)

---

## Branch: 15.0

All items from the 16.0 checklist apply. Additional 15.0-specific items:

### OWL 1 JS component — UNVERIFIED items

- [ ] **[UNVERIFIED]** `useService("orm")` called inside `setup()` resolves correctly in
      Odoo 15. If it throws `"Service 'orm' is not available"` or similar, the alternative
      is to replace `this.orm = useService("orm")` with `this.orm = this.env.services.orm`
      (accessing services via the environment object, the pre-hook pattern).
- [ ] **[UNVERIFIED]** `this.refs.reader` and `this.refs.result` are populated after
      `mounted()` is called. In OWL 1, `t-ref` DOM refs were accessible as
      `this.__owl__.refs` or `this.refs` depending on the exact OWL 1.x minor version
      bundled with Odoo 15. If `this.refs.reader` is undefined in mounted(), try
      `this.__owl__.refs.reader` instead, or pin to the Odoo 15 community module pattern.
- [ ] **[UNVERIFIED]** `async mounted()` is called by OWL 1 after the component's first
      render. Verify in browser console that `loadQrCodeScanner()` is called. If not,
      rename to `async willStart()` (which runs before first render) or add explicit
      `connectedCallback` depending on the exact OWL 1 version.
- [ ] Scanner JS loads without `TypeError: Cannot read properties of undefined` on
      `self.refs.reader` — if it does, the refs API differs; see UNVERIFIED note above.

### Python environment

- [ ] `qrcode` package compatible with the Python version bundled in Odoo 15
      (Odoo 15 requires Python 3.8+; `qrcode[pil]` works on 3.8)
- [ ] `Pillow` (required by `qrcode[pil]`) is installed in the Odoo 15 virtualenv

### `assets` key in manifest

- [ ] Confirm Odoo 15 recognises the `assets` key in `__manifest__.py`. This was
      introduced in Odoo 15.0 as part of the new asset bundling system. If on an early
      Odoo 15.0 patch release, check whether the new asset system was included.
      If not recognised, assets must be declared via XML `<template>` inheriting
      `web.assets_backend` instead.

### Views

- [ ] `attrs` domain syntax (converted in 16.0 and carried over) still works correctly.
      Odoo 15 uses `attrs` exclusively — confirm no inline-Python expression leaked back.

### Report

- [ ] `web.basic_layout` renders correctly in Odoo 15. This template existed before 15
      so it should be fine, but verify the PDF header/footer behaviour matches expectations.

---

## Items that cannot be tested by static analysis on ANY branch

- QR code image generation (depends on `qrcode` library and Pillow at runtime)
- PDF rendering (depends on wkhtmltopdf version and Odoo paper format config)
- Camera/webcam QR scanning (browser permission + `html5-qrcode` library compatibility)
- `ir.sequence` number assignment (requires a running database)
- Menu and action resolution (requires Odoo XML loading pipeline)
- Asset bundling / JS module loading (requires Odoo asset pipeline)

---

*Generated: 2026-07-01. Test in an isolated staging database before publishing.*
