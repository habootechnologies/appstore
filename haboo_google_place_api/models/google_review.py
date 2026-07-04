# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import requests
import os
import json
import logging
from google.auth.transport.requests import Request
import google.auth.transport.requests 
from dateutil import parser as date_parser
from datetime import datetime

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_client_id = fields.Char("Google Client ID", config_parameter='haboo_google_place_api.google_client_id')
    google_client_secret = fields.Char("Google Client Secret", config_parameter='haboo_google_place_api.google_client_secret')
    google_redirect_uri = fields.Char("Google Redirect URI", config_parameter='haboo_google_place_api.google_redirect_uri')
    google_access_token = fields.Char("Access Token", config_parameter='haboo_google_place_api.google_access_token')
    google_refresh_token = fields.Char("Refresh Token", config_parameter='haboo_google_place_api.google_refresh_token')
    google_token_expiry_seconds = fields.Char("Token Expiry (seconds)", config_parameter='haboo_google_place_api.google_token_expiry_seconds')
    scheduler_record_limit = fields.Selection(
        selection=[('50', '50'), ('100', '100'), ('150', '150'), ('200', '200'), ('250', '250'), ('300', '300'), ('350', '350'), ('400', '400'), ('450', '450'), ('500', '500')],
        string="Scheduler Record Limit",
        config_parameter='haboo_google_place_api.scheduler_record_limit',
        default='50'
    )
    
    def action_connect_google(self):
        self.ensure_one()
        full_url = f"{self.google_redirect_uri}google/oauth"
        return {
            'type': 'ir.actions.act_url',
            'url': full_url,
            'target': 'new',
        }

    def get_all_reviews(self):
        self.env['google.review'].get_google_reviews(mode='full') 

class GoogleReviews(models.Model):
    _name = 'google.review'
    _inherit = ['mail.thread']
    _description = 'Google Reviews'
    _order = 'review_updated_time desc'

    name = fields.Char(default='New', readonly=True, copy=False)
    review_author_name = fields.Char(string="Review Author Name")
    location_name = fields.Char(string="location")
    administrativeArea = fields.Char(string="Area")
    locality = fields.Char(string="locality")
    addressLines = fields.Char(string="Address")
    original_text = fields.Text(string="Message")
    review_id = fields.Char(string="Review Id")
    regionCode = fields.Char(string="Region Code")
    postalCode = fields.Char(string="Postal Code")
    replay_msg = fields.Char(string="Reply")
    review_name = fields.Char(string="Review Name")
    review_time = fields.Datetime(string="Review Time")
    review_updated_time = fields.Datetime(string="Review Updated Time")
    replay_time = fields.Datetime(string="Reply Time")
    replay_updated_time = fields.Datetime(string="Reply Updated Time")
    priority = fields.Selection([('0', 'Zero'), ('1', 'ONE'), ('2', 'TWO'), ('3', 'THREE'), ('4', 'FOUR'), ('5', 'FIVE')], string='Ratings', index=True, default='0')
    readonly_review = fields.Boolean(string="Readonly review", default=True)

    def to_naive_datetime(self, dt_str):
        if dt_str:
            dt = date_parser.parse(dt_str)
            if dt.tzinfo:
                dt = dt.astimezone(tz=None).replace(tzinfo=None)
            return dt
        return False
        
    def get_access_token(self):
        config = self.env['ir.config_parameter'].sudo()
        google_redirect_uri = config.get_param('haboo_google_place_api.google_redirect_uri')

        if not google_redirect_uri:
            _logger.warning("Google redirect URI is missing.")
            return False

        access_token_uri = f"{google_redirect_uri}google/access_token"

        try:
            response = requests.get(access_token_uri, timeout=10)
            if response.status_code != 200:
                _logger.error("Failed to retrieve access token. Status: %s, Response: %s", response.status_code, response.text)
                return False

            token_data = response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                _logger.error("Access token not found in response: %s", token_data)
                return False

            return access_token

        except requests.exceptions.RequestException as e:
            _logger.exception("Exception while trying to get Google access token: %s", str(e))
            return False

    def action_edit_review(self):
        self.readonly_review = False

    def action_cancle(self):
        self.readonly_review = True
        self.replay_msg = False

    def action_delete_review(self):
        access_token = self.get_access_token()
        if not access_token:
            _logger.error("Access token missing while trying to delete review replies.")
            return {'success': False, 'error': 'Access token missing'}

        for review in self:
            try:
                url = f"https://mybusiness.googleapis.com/v4/{review.review_name}/reply"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                response = requests.delete(url, headers=headers)
                if response.status_code == 200:
                    # self.refresh_values(access_token)
                    self.replay_msg = False
                    self.replay_updated_time = False
                    _logger.info("Reply deleted for review ID: %s", review.name)
                    return {'success': True, 'message': 'Reply deleted successfully.'}
                else:
                    _logger.error("Failed to delete reply for %s: %s", review.name, response.text)
                    return {
                        'success': False,
                        'error': 'Failed to delete reply',
                        'details': response.text
                    }
            except Exception as e:
                _logger.exception("Exception while deleting reply for review ID: %s", review.name)
                return {
                    'success': False,
                    'error': 'Internal server error',
                    'message': str(e)
                }

    def action_reply_review(self):
        access_token = self.get_access_token()
        if not access_token:
            _logger.error("Access token missing while trying to post review reply.")
            return {'success': False, 'error': 'Access token missing'}

        for review in self:
            if not review.replay_msg:
                _logger.warning("Replay message is missing for review ID: %s", review.name)
                return {'success': False, 'error': 'Replay message is required.'}

            try:
                url = f"https://mybusiness.googleapis.com/v4/{review.review_name}/reply"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "comment": review.replay_msg
                }
                _logger.info("Sending reply to review ID %s: %s", review.name, payload)

                response = requests.put(url, headers=headers, json=payload)

                if response.status_code == 200:
                    review.readonly_review = True
                    review.review_updated_time = fields.Datetime.now()
                    _logger.info("Reply successfully posted for review ID: %s", review.name)
                    return {'success': True, 'message': 'Reply posted successfully.'}
                else:
                    _logger.error("Failed to post reply for %s: %s", review.name, response.text)
                    return {
                        'success': False,
                        'error': 'Failed to reply',
                        'details': response.text
                    }
            except Exception as e:
                _logger.exception("Exception while replying to review ID: %s", review.name)
                return {
                    'success': False,
                    'error': 'Internal server error',
                    'message': str(e)
                }

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('google.review.code') or ('New')
        return super(GoogleReviews, self).create(vals)

    def get_the_ratings(self, starRating):
        if starRating == 'ONE':
            ratings = '1'
        elif starRating == 'TWO':
            ratings = '2'
        elif starRating== 'THREE':
            ratings = '3'
        elif starRating == 'FOUR':
            ratings = '4'
        elif starRating == 'FIVE':
            ratings = '5'
        else:
            ratings = '0'
        return ratings 

    def get_google_accounts(self, access_token):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        url = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code != 200:
                _logger.warning("Failed to fetch accounts: %s", response.text)
                return []
            return response.json().get("accounts", [])
        except Exception as e:
            _logger.exception("Error occurred while fetching Google accounts: %s", str(e))
            return []

    def get_google_locations(self, account_id, access_token):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{account_id}/locations"
        try:
            response = requests.get(url, headers=headers, params={
                "readMask": "name,title,storefrontAddress",
                "pageSize": 50
            })
            if response.status_code != 200:
                _logger.warning("Failed to fetch locations for account %s: %s", account_id, response.text)
                return []
            return response.json().get("locations", [])
        except Exception as e:
            _logger.exception("Error occurred while fetching locations for account %s: %s", account_id, str(e))
            return []

    def get_all_reviews_for_location(self, full_location_name, location_display_name, access_token):
        config = self.env['ir.config_parameter'].sudo()
        scheduler_record_limit = config.get_param('haboo_google_place_api.scheduler_record_limit', '100')
        
        try:
            scheduler_record_limit = int(scheduler_record_limit)
        except ValueError:
            _logger.warning("Invalid scheduler_record_limit value. Falling back to 100.")
            scheduler_record_limit = 100

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        reviews = []
        page_token = None

        try:
            while True:
                remaining = scheduler_record_limit - len(reviews)
                if remaining <= 0:
                    break

                params = {"pageSize": min(50, remaining)}
                if page_token:
                    params["pageToken"] = page_token

                url = f"https://mybusiness.googleapis.com/v4/{full_location_name}/reviews"
                response = requests.get(url, headers=headers, params=params)

                if response.status_code != 200:
                    _logger.warning("Could not fetch reviews for %s: %s", full_location_name, response.text)
                    break

                data = response.json()
                fetched_reviews = data.get("reviews", [])
                reviews.extend(fetched_reviews)

                page_token = data.get("nextPageToken")
                if not page_token or len(reviews) >= scheduler_record_limit:
                    break

            _logger.info("Fetched %d reviews for location %s", len(reviews), location_display_name)
            return reviews[:scheduler_record_limit]

        except Exception as e:
            _logger.exception("Error while fetching reviews for location %s: %s", full_location_name, str(e))
            return []

    def get_all_reviews_for_location_full(self, full_location_name, location_display_name,access_token):
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }

        reviews = []
        page_token = None

        try:
            while True:
                params = {"pageSize": 50}
                if page_token:
                    params["pageToken"] = page_token

                url = f"https://mybusiness.googleapis.com/v4/{full_location_name}/reviews"
                response = requests.get(url, headers=headers, params=params)

                if response.status_code != 200:
                    _logger.warning("Could not fetch reviews for %s: %s", full_location_name, response.text)
                    break

                data = response.json()
                reviews.extend(data.get("reviews", []))
                page_token = data.get("nextPageToken")
                if not page_token:
                    break

            _logger.info("Fetched %d reviews for location %s", len(reviews), location_display_name)
            return reviews

        except Exception as e:
            _logger.exception("Error while fetching all reviews for location %s: %s", full_location_name, str(e))
            return []

    def prepare_review_vals(self, rec):
        review_create_dt = self.to_naive_datetime(rec.get('createTime'))
        review_update_dt = self.to_naive_datetime(rec.get('updateTime'))
        reviewReply = rec.get('reviewReply', {})
        replay_create_dt = self.to_naive_datetime(reviewReply.get('createTime')) if reviewReply else False
        replay_update_dt = self.to_naive_datetime(reviewReply.get('updateTime')) if reviewReply else False
        reviewReplyComment = reviewReply.get('comment') if reviewReply else False
        ratings = self.get_the_ratings(rec.get('starRating'))

        return {
            "review_id": rec.get('reviewId'),
            "priority": ratings,
            "review_name": rec.get('name'),
            "original_text": rec.get("comment"),
            "review_author_name": rec.get("reviewer", {}).get("displayName", "Anonymous"),
            "review_time": review_create_dt,
            "review_updated_time": review_update_dt,
            "replay_msg": reviewReplyComment,
            "replay_time": replay_create_dt,
            "replay_updated_time": replay_update_dt,
        }

    def _normalize(self, value):
        """Convert None, False, and empty values to empty string for safe comparison."""
        return value or ''

    @api.model
    def get_google_reviews(self, mode):
        access_token = self.get_access_token()
        if not access_token:
            _logger.warning("Access token is missing. Skipping review sync.")

        accounts = self.get_google_accounts(access_token)
        if not accounts:
            _logger.warning("No Google accounts found. Skipping review sync.")
        account_id = accounts[0]["name"]

        locations = self.get_google_locations(account_id, access_token)
        if not locations:
            _logger.warning("No locations found for account %s. Skipping review sync.", account_id)

        all_reviews = []
        for loc in locations:
            administrativeArea = False
            locality = False
            regionCode = False
            addressLines = False
            postalCode = False
            location_resource = loc.get("name")
            location_display_name = loc.get("title")
            storefrontAddress = loc.get("storefrontAddress")
            if storefrontAddress:
                administrativeArea = storefrontAddress.get('administrativeArea')
                locality = storefrontAddress.get('locality')
                addressLines = storefrontAddress.get('addressLines')
                postalCode = storefrontAddress.get('postalCode')
                regionCode = storefrontAddress.get('regionCode')

            full_location_path = f"{account_id}/{location_resource}"
            if mode == 'full':
                reviews = self.get_all_reviews_for_location_full(full_location_path, location_display_name,access_token)
            else:
                reviews = self.get_all_reviews_for_location(full_location_path, location_display_name,access_token)

            for rec in reviews:
                rec["location_display_name"] = location_display_name
                rec["administrativeArea"] = administrativeArea
                rec["locality"] = locality
                rec["postalCode"] = postalCode
                rec["regionCode"] = regionCode
                rec["addressLines"] = addressLines[0] if addressLines else False

            all_reviews.extend(reviews)

        review_model = self.env['google.review']
        existing_reviews = review_model.search([('review_id', 'in', [r.get('reviewId') for r in all_reviews])])
        existing_review_map = {r.review_id: r for r in existing_reviews}

        to_create = []
        to_update = []

        for rec in all_reviews:
            # _logger.info("reviewssssss==================%s", rec)
            review_id = rec.get('reviewId')
            review_create_dt = self.to_naive_datetime(rec.get('createTime'))
            review_update_dt = self.to_naive_datetime(rec.get('updateTime'))
            reviewReply = rec.get('reviewReply', {})
            replay_create_dt = self.to_naive_datetime(reviewReply.get('createTime')) if reviewReply else False
            replay_update_dt = self.to_naive_datetime(reviewReply.get('updateTime')) if reviewReply else False
            reviewReplyComment = reviewReply.get('comment') if reviewReply else False
            ratings = self.get_the_ratings(rec.get('starRating'))

            vals = {
                "review_id": review_id,
                "priority": ratings,
                "review_name": rec.get('name'),
                "original_text": rec.get("comment"),
                "review_author_name": rec.get("reviewer", {}).get("displayName", "Anonymous"),
                "review_time": review_create_dt,
                "review_updated_time": review_update_dt,
                "replay_msg": reviewReplyComment,
                "replay_time": replay_create_dt,
                "replay_updated_time": replay_update_dt,
                "location_name": rec.get("location_display_name"),
                "administrativeArea": rec.get("administrativeArea"),
                "locality": rec.get("locality"),
                "addressLines": rec.get("addressLines"),
                "regionCode": rec.get("regionCode"),
                "postalCode": rec.get("postalCode"),
            }

            existing = existing_review_map.get(review_id)
            if existing:
                needs_update = any([
                    self._normalize(reviewReplyComment) != self._normalize(existing.replay_msg),
                    self._normalize(review_create_dt) != self._normalize(existing.review_time),
                    self._normalize(review_update_dt) != self._normalize(existing.review_updated_time),
                    self._normalize(replay_create_dt) != self._normalize(existing.replay_time),
                    self._normalize(replay_update_dt) != self._normalize(existing.replay_updated_time),
                    self._normalize(rec.get("comment")) != self._normalize(existing.original_text),
                    self._normalize(existing.priority) != self._normalize(ratings),
                    self._normalize(existing.location_name) != self._normalize(vals.get("location_name")),
                    self._normalize(existing.administrativeArea) != self._normalize(vals.get("administrativeArea")),
                    self._normalize(existing.locality) != self._normalize(vals.get("locality")),
                    self._normalize(existing.postalCode) != self._normalize(vals.get("postalCode")),
                    self._normalize(existing.regionCode) != self._normalize(vals.get("regionCode")),
                    self._normalize(existing.addressLines) != self._normalize(vals.get("addressLines")),
                ])
                if needs_update:
                    to_update.append((existing, vals))
            else:
                to_create.append(vals)

        messages_to_create = []
        for record, vals in to_update:
            messages_to_create.append({
                "message_type": 'comment',
                'model': 'google.review',
                'res_id': record.id,
                "body": "Review Is Updated",
            })
            # self.mail_message_send(record.id, "Review Is Updated")
            record.write(vals)

        if messages_to_create:
            self.env['mail.message'].sudo().create(messages_to_create) 
        
        if to_create:
            google_review_ids = review_model.create(to_create)
    
        _logger.info("Google review sync completed. Created: %d, Updated: %d", len(to_create), len(to_update))
