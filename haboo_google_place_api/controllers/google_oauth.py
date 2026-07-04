import logging
from odoo import http
from odoo.http import request, Response
from google_auth_oauthlib.flow import Flow
import requests
import json
from werkzeug.utils import redirect

_logger = logging.getLogger(__name__)

class GoogleOAuthController(http.Controller):
    @http.route('/google/oauth', auth='public')
    def google_auth(self, **kw):
        config = request.env['ir.config_parameter'].sudo()
        client_id = config.get_param('haboo_google_place_api.google_client_id')
        google_redirect_uri = config.get_param('haboo_google_place_api.google_redirect_uri')
        redirect_uri = f"{google_redirect_uri}google/oauth/callback"
        scope = "https://www.googleapis.com/auth/business.manage"
        if not client_id or not google_redirect_uri:
            if not client_id:
                _logger.exception("Client id is Missing")
            elif not google_redirect_uri:
                _logger.exception("Google Redirect Url is Missing")
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"response_type=code&client_id={client_id}"
            f"&redirect_uri={redirect_uri}&scope={scope}&access_type=offline&prompt=consent"
        )
        # _logger.info("\n Redirecting user to Google OAuth URL: %s", auth_url)
        return redirect(auth_url)

    @http.route('/google/access_token', type='http', auth='public', methods=['GET'], csrf=False)
    def get_google_access_token(self):
        """Refresh and return a valid Google access token."""
        config = request.env['ir.config_parameter'].sudo()
        client_id = config.get_param('haboo_google_place_api.google_client_id')
        client_secret = config.get_param('haboo_google_place_api.google_client_secret')
        refresh_token = config.get_param('haboo_google_place_api.google_refresh_token')

        if not client_id or not client_secret or not refresh_token:
            if not client_id:
                _logger.exception("Client ID is missing")
            if not client_secret:
                _logger.exception("Client Secret is missing")
            if not refresh_token:
                _logger.exception("Refresh Token is missing")
            return json.dumps({
                'error': 'Missing required configuration parameters.'
            })
        payload = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': refresh_token,
            'grant_type': 'refresh_token',
        }
        try:
            response = requests.post('https://oauth2.googleapis.com/token', data=payload)
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)

                config.set_param("haboo_google_place_api.google_access_token", access_token)
                config.set_param("haboo_google_place_api.google_token_expiry_seconds", str(expires_in))

                return json.dumps({
                    'access_token': access_token,
                    'expires_in': expires_in
                })
            else:
                _logger.error("Token refresh failed: %s", response.text)
                return json.dumps({
                    'error': 'Token refresh failed.',
                    'details': response.text
                })
        except Exception as e:
            _logger.exception("Exception in access token controller: %s", str(e))
            return json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })

    @http.route('/google/oauth/callback', type='http', auth='public', csrf=False)
    def google_callback(self, code=None, error=None, **kwargs):
        config = request.env['ir.config_parameter'].sudo()
        scope = "https://www.googleapis.com/auth/business.manage"

        if error:
            _logger.error("OAuth error from Google: %s", error)
            return "Google OAuth failed: %s" % error

        if not code:
            _logger.error("No authorization code received.")
            return "Missing authorization code."

        client_id = config.get_param('haboo_google_place_api.google_client_id')
        client_secret = config.get_param('haboo_google_place_api.google_client_secret')
        google_redirect_uri = config.get_param('haboo_google_place_api.google_redirect_uri')
        redirect_uri = f"{google_redirect_uri}google/oauth/callback"
        token_url = "https://oauth2.googleapis.com/token"

        payload = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }

        try:
            response = requests.post(token_url, data=payload)
            token_info = response.json()

            if 'error' in token_info:
                _logger.error("Google returned error: %s", token_info)
                return "OAuth failed: %s" % token_info.get('error_description', 'Unknown error')

            access_token = token_info.get("access_token")
            refresh_token = token_info.get("refresh_token")
            expires_in = token_info.get("expires_in")

            if access_token:
                config = request.env['ir.config_parameter'].sudo()
                config.set_param("haboo_google_place_api.google_access_token", access_token)
                access_token_param = request.env['ir.config_parameter'].sudo().get_param('haboo_google_place_api.google_access_token')

                if refresh_token:
                    config.set_param("haboo_google_place_api.google_refresh_token", refresh_token)
                    access_token_refresh_param = request.env['ir.config_parameter'].sudo().get_param('haboo_google_place_api.google_refresh_token')

                if expires_in:
                    config.set_param("haboo_google_place_api.google_token_expiry_seconds", str(expires_in))

                return "OAuth authentication successful. You may close this window."

            _logger.error("No access token received. Token info: %s", token_info)
            return "OAuth failed: Access token not found."

        except Exception as e:
            _logger.exception("Exception occurred during token exchange: %s", str(e))
            return "OAuth failed due to internal error."


    @http.route('/send/google_replay', type='json', auth='user')
    def send_google_replay(self, res_id=None, body=None, **kwargs):
        if not res_id or not body:
            return {'success': False, 'error': 'Missing res_id or body'}

        review = request.env['google.review'].sudo().browse(res_id)
        if not review.exists():
            return {'success': False, 'error': 'Review not found'}

        config = request.env['ir.config_parameter'].sudo()
        google_redirect_uri = config.get_param('haboo_google_place_api.google_redirect_uri')
        access_token_uri = f"{google_redirect_uri}google/access_token"

        if not google_redirect_uri:
            _logger.error("Google redirect URI not configured.")
            return {'success': False, 'error': 'Google redirect URI is missing.'}

        try:
            token_response = requests.get(access_token_uri, timeout=10)
            token_data = token_response.json()
        except Exception as e:
            _logger.exception("Failed to get token from token controller")
            return {'success': False, 'error': 'Token fetch failed', 'message': str(e)}

        access_token = token_data.get("access_token")
        if not access_token:
            return {'success': False, 'error': 'No access token', 'message': token_data.get('error')}

        if not review.review_name:
            return {'success': False, 'error': 'Missing review_name in record'}

        # Send reply to Google
        try:
            url = f"https://mybusiness.googleapis.com/v4/{review.review_name}/reply"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            payload = {"comment": body}

            _logger.info("Sending Google review reply: %s", payload)
            response = requests.put(url, headers=headers, json=payload)

            if response.status_code == 200:
                return {'success': True, 'message': 'Reply posted successfully.', 'status': 200}
            else:
                _logger.error("Google reply failed: %s", response.text)
                return {
                    'success': False,
                    'error': 'Reply failed',
                    'status': response.status_code,
                    'details': response.text,
                }

        except Exception as e:
            _logger.exception("Exception during reply post")
            return {
                'success': False,
                'error': 'Internal error',
                'message': str(e),
                'status': 400,
            }

