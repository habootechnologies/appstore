from odoo import models, fields, api
import requests
from odoo.exceptions import UserError
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)
import base64
from odoo.addons.html_editor.tools import get_video_embed_code, get_video_thumbnail

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    instagram_post_limit = fields.Selection(
        selection=[('50', '50'), ('100', '100'), ('150', '150'), ('200', '200'), ('250', '250'), ('300', '300'), ('350', '350'), ('400', '400'), ('450', '450'), ('500', '500')],
        string="Instagram post fetch limit",
        config_parameter='haboo_facebook_instagram_integration.instagram_post_limit',
        default='50'
    )

class InstagramPost(models.Model):
    _name = 'post.post'
    _description = 'Instagram | Facebook Post'
    _rec_name = 'caption'
    
    post_id = fields.Char('Post ID')
    caption = fields.Text('Caption')
    media_url = fields.Char('Media URL')
    thumbnail_url = fields.Char()
    media_type = fields.Char()
    permalink = fields.Char()
    comment_ids = fields.One2many('post.comments', 'post_id', string='Comments')
    is_sponsored = fields.Boolean('Is Sponsored')
    owner = fields.Char('Owner')
    username = fields.Char('Username')
    all_comment_texts = fields.Text(
        string='All Comment Texts', 
        compute='_compute_all_comment_texts', 
        store=False
    )
    meta_platform = fields.Selection([('instagram', 'Instagram'), ('facebook', 'Facebook')], default='instagram')
    caption_first_line = fields.Char(
        string='Caption (First Line)',
        compute='_compute_caption_first_line',
        store=False
    )
    latest_comment_timestamp = fields.Datetime(
        string="Latest Comment Timestamp",
        compute="_compute_latest_comment_timestamp",
        store=True
    )
    last_activity = fields.Datetime("Last Activity", default=fields.Datetime.now)



    @api.depends('comment_ids.text')
    def _compute_all_comment_texts(self):
        for post in self:
            text_list = []
            if post.comment_ids:
                text_list = [c.text if c.text else '' for c in post.comment_ids]
            post.all_comment_texts = "\n\n".join(text_list)


    @api.depends('caption')
    def _compute_caption_first_line(self):
        for post in self:
            if post.caption:
                post.caption_first_line = post.caption.split('\n', 1)[0]  # get only first line
            else:
                post.caption_first_line = ''

    @api.depends('comment_ids.timestamp')
    def _compute_latest_comment_timestamp(self):
        for post in self:
            if post.comment_ids:
                latest_ts = max(post.comment_ids.mapped('timestamp'))
                post.latest_comment_timestamp = latest_ts
            else:
                post.latest_comment_timestamp = False

    def fetch_comments(self):
        Provider = self.env['provider'].sudo()
        account = Provider.search([
            ('graph_api_authenticated', '=', True),
            ('meta_platform', '=', self.meta_platform)
        ], limit=1)
        if not account:
            raise UserError("No authenticated provider found.")
        token = account.graph_api_token
        if self.meta_platform == "facebook":
             token = account.facebook_page_token
        self.fetch_comments_for_post(self ,token, self.meta_platform)
        return True

    def get_post_and_comments(self, mode='full', platform="instagram"):
        print(platform)
        self.fetch_posts_and_comments(mode=mode, platform=platform)

    def get_accounts(self, platform):
        config = self.env['ir.config_parameter'].sudo()
        fetch_limit = int(config.get_param('haboo_facebook_instagram_integration.instagram_post_limit', 200))
        Provider = self.env['provider'].sudo()
        account = Provider.search([
            ('graph_api_authenticated', '=', True),
            ('meta_platform', '=', platform)
        ], limit=1)
        url = False
        if platform == "facebook":
            url = f"https://graph.facebook.com/v24.0/{account.account_id}/posts"
        else:
            url = f"https://graph.instagram.com/v24.0/{account.instagram_business_account_id}/media"
        return account, url, fetch_limit 


    def fetch_posts_and_comments(self, mode='full', platform="instagram"):
        """Fetch posts and comments from all connected Instagram provider accounts safely"""
        print(platform)
        account, url, fatch_limit = self.get_accounts(platform=platform)
        limit = 0
        counter_limit = 0
        print("comments .........................", platform)
        if mode != "full":
            limit = fatch_limit
        try:
            all_posts = []
            params = {
                'fields': 'id,caption,media_type,media_url,permalink,thumbnail_url,is_sponsored,owner,username',
                'access_token': account.graph_api_token,
            }
            if platform == "facebook":
                params = {
                    'fields': 'id,permalink_url,from,attachments,message,actions',
                    'access_token': account.graph_api_token,
                }

            while url:
                counter_limit += 25
                print(url, params)
                response_posts = requests.get(url, params=params, timeout=50)
                # Access the headers
                headers = response_posts.headers

                # Print all headers
                print("All Response Headers:")
                for header, value in headers.items():
                    print(f"{header}: {value}")
                response_posts.raise_for_status()
                data = response_posts.json()
                all_posts.extend(data.get('data', []))
                if 'paging' in data and 'next' in data['paging']:
                    url = data['paging']['next']
                    params = {}
                else:
                    url = None
                print(limit, type(limit))
                if limit > 0 and limit <= counter_limit:
                    print("Broken by limit")
                    url = None
            _logger.info("Fetched %d posts for account %s", len(all_posts), account.instagram_business_account_id)

            # ===============================
            # Store posts and fetch comments
            # ===============================
            for p in all_posts:
                print(p)
                print("=========================================================================================================")
                post_id = p.get('id')
                if not post_id:
                    _logger.warning("Skipping post with missing ID: %s", p)
                    continue
                # target = p.get("target")
                # if target:
                #     post_id = target.get("id")
                post_record = self.search([('post_id', '=', post_id)], limit=1)
                if platform == "instagram":
                    data_to_write = {
                        'post_id': post_id,
                        'permalink': p.get('permalink', ''),
                        'media_url': p.get('media_url', ''),
                        'caption': p.get('caption', ''),
                        'meta_platform': platform,
                        'thumbnail_url' : p.get('thumbnail_url',''),
                        'media_type': p.get('media_type',''),
                        'is_sponsored': p.get('is_sponsored', False),
                        'owner': p.get('owner', {}).get('id') if p.get('owner') else False,
                        'username': p.get('username', '')}

                else:

                    username = ''
                    if p.get('from'):
                        username = p.get('from').get('name', '')
                    data = p.get('attachments').get('data')[0]
                    media = data.get('media',)
                    image = media.get('image', '')
                    data_to_write = {
                        'post_id': post_id,
                        'meta_platform': platform,
                        'permalink': p.get('permalink_url', ''),
                        'username': username,
                        'media_type': data.get('type', ''),
                        'media_url': image.get('src', ''),
                        'caption': p.get('message', '')
                        }
                if not post_record:
                    post_record = self.sudo().create(data_to_write)
                else:
                    post_record.sudo().write(data_to_write)
                token = account.graph_api_token
                if platform == "facebook":
                    token = account.facebook_page_token
                self.fetch_comments_for_post(post_record, token, platform=platform)
        except requests.exceptions.RequestException as e:
            _logger.error("Failed to fetch posts/comments: %s", e)
        except Exception as e:
            _logger.error("Unexpected error fetching posts/comments: %s", e)

    def fetch_comments_for_post(self, post_record, access_token, platform):
        try:
            url = f'https://graph.instagram.com/v24.0/{post_record.post_id}/comments'
            print(access_token)
            comments_data = []
            params = {
                'fields': 'id,text,timestamp,username,from',
                'sort': 'newest_to_oldest',
                'access_token': access_token,
            }
            if platform == "facebook":
                url = f'https://graph.facebook.com/v24.0/{post_record.post_id}/comments'
                params = {
                    'fields': 'id,message,from,created_time',
                    'access_token': access_token,
                }

            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            comments_data.extend(data.get('data', []))
            if comments_data:
                print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
                print(comments_data)
                print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
            for c in comments_data:
                comment_id = c.get('id')
                if not comment_id:
                    continue
                ts = c.get('timestamp', c.get('created_time'))
                timestamp_val = False
                if ts:
                    try:
                        timestamp_val = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
                        timestamp_val = timestamp_val.replace(tzinfo=None)
                    except Exception as e:
                        _logger.error("Failed to parse comment timestamp %s: %s", ts, e)
                        timestamp_val = False
                comment_record = self.env['post.comments'].search([('comment_id', '=', comment_id)], limit=1)
                username = ''
                if c.get('from'):
                    username = c.get('from').get('username', '')
                comment_data = {
                    'post_id': post_record.id,
                    'comment_id': comment_id,
                    'text': c.get('text', c.get('message', '')) or c,
                    'username': username,
                    'timestamp': timestamp_val,
                    'parent_id': False,
                }
                if not comment_record:
                    if username not in ['giriindia_', 'GiriIndia1951']:
                        comment_record = self.env['post.comments'].create(comment_data)
                else:
                    comment_record.write(comment_data)
                if comment_record:
                    if platform == "instagram":
                        self.fetch_comment_replies(comment_record, access_token, platform)
                        print("OK")
            _logger.info("Fetched %d comments for post %s ", len(comments_data), post_record.post_id)
        except requests.exceptions.RequestException as e:
            _logger.error("Failed to fetch comments for post %s: %s", post_record.post_id, e)
        except Exception as e:
            _logger.error("Unexpected error fetching comments for post %s: %s", post_record.post_id, e)

    def fetch_comment_replies(self, comment_record, access_token, platform):
        """
        Fetch replies from Instagram and store in post.comment.reply
        """
        try:
            replies = []
            url = f'https://graph.instagram.com/v24.0/{comment_record.comment_id}/replies'
            if platform == "facebook":
                url = f'https://graph.facebook.com/v24.0/{comment_record.comment_id}/replies'
            params = {
                'fields': 'id,text,timestamp,username',
                'sort': 'newest_to_oldest',
                'access_token': access_token,
            }
            response = requests.get(url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            print(data, len(data))
            replies.extend(data.get('data', []))
            for r in replies:
                reply_id = r.get('id')
                if not reply_id:
                    continue

                ts = r.get('timestamp')
                timestamp_val = None
                if ts:
                    try:
                        timestamp_val = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
                    except Exception as e:
                        _logger.error("Failed to parse reply timestamp %s: %s", ts, e)
                existing = self.env['post.comment.reply'].search([('reply_id', '=', reply_id)], limit=1)
                replies = {
                    'comment_id': comment_record.id,
                    'reply_id': reply_id,
                    'text': r.get('text', ''),
                    'username': r.get('username', ''),
                    'timestamp': timestamp_val,
                }
                if not existing:
                    self.env['post.comment.reply'].create(replies)
                else:
                    existing.write(replies)
            _logger.info("Fetched replies for comments %s", comment_record.comment_id)
        except Exception as e:
            _logger.error("Error fetching replies for comments %s: %s", comment_record.comment_id, e)


class InstagramCommentReply(models.Model):
    _name = 'post.comment.reply'
    _description = 'Instagram Post Comment Reply'

    comment_id = fields.Many2one('post.comments', string='Parent Comment', ondelete='cascade', required=True)
    reply_id = fields.Char('Reply ID')
    text = fields.Text('Reply Text')
    username = fields.Char('Username')
    timestamp = fields.Datetime('Timestamp')
    reply_text = fields.Text('Reply Text')
    post_id = fields.Many2one('post.post', string='Post', related='comment_id.post_id', store=True)


    def delete_reply(self):
        Provider = self.env['provider'].sudo()
        account = Provider.search([
            ('graph_api_authenticated', '=', True),
            ('meta_platform', '=', 'instagram')
        ], limit=1)
        if not account:
            raise UserError("No authenticated Instagram provider found.")
        try:
            url = f'https://graph.instagram.com/'+self.comment_id
            params = {
                'access_token': access_token
            }
            response = requests.delete(url, params=params)
            response_data = response.json()
            _logger.info("Delete %d data for comments %s ", len(response_data), self.comment_id)
            if response.status_code == 200 and 'success' in response_data and response_data['success'] == True:
                self.unlink()
        except requests.exceptions.RequestException as e:
            _logger.error("Failed to delete comments for replay %s: %s", self.comment_id, e)
        except Exception as e:
            _logger.error("Unexpected error during deleting reply %s: %s", self.comment_id, e)
        return True

    # def fetch_comment_replies(self, post_record, access_token):
    #     """
    #     Fetch replies from Instagram and store in post.comment.reply
    #     """
    #     try:
    #         comments = self.env['post.comments'].search([('post_id', '=', post_record.id)])
    #         self.comment_id
    #             replies = []
    #             url = f'https://graph.instagram.com/v24.0/{comment.comment_id}/replies'
    #             params = {
    #                 'fields': 'id,text,timestamp,username',
    #                 'access_token': access_token,
    #             }
    #             response = requests.get(url, params=params, timeout=60)
    #             response.raise_for_status()
    #             data = response.json()
    #             print(data, len(data))
    #             replies.extend(data.get('data', []))
    #             for r in replies:
    #                 reply_id = r.get('id')
    #                 if not reply_id:
    #                     continue

    #                 ts = r.get('timestamp')
    #                 timestamp_val = None
    #                 if ts:
    #                     try:
    #                         timestamp_val = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").replace(tzinfo=None)
    #                     except Exception as e:
    #                         _logger.error("Failed to parse reply timestamp %s: %s", ts, e)

    #                 existing = self.search([('reply_id', '=', reply_id)], limit=1)
    #                 replies = {
    #                     'comment_id': comment.id,
    #                     'reply_id': reply_id,
    #                     'text': r.get('text', ''),
    #                     'username': r.get('username', ''),
    #                     'timestamp': timestamp_val,
    #                 }
    #                 if not existing:
    #                     self.create(replies)
    #                 else:
    #                     existing.write(replies)

    #         _logger.info("Fetched replies for post %s", post_record.post_id)

    #     except Exception as e:
    #         _logger.error("Error fetching replies for post %s: %s", post_record.post_id, e)

class InstagramComment(models.Model):
    _name = 'post.comments'
    _description = 'Post Comment | Instagram | Facebook'

    post_id = fields.Many2one('post.post', string='Post', ondelete='cascade')
    comment_id = fields.Char('Comment ID')
    text = fields.Text('Comment Text')
    username = fields.Char('Username')
    parent_id = fields.Many2one('post.comments', string='Parent Comment')
    reply_ids = fields.One2many('post.comment.reply', 'comment_id', string='Replies')
    timestamp = fields.Datetime('Timestamp')
    reply_text = fields.Text('Reply Text')
    partner_id = fields.Many2one("res.partner", "Partner")
    post_caption = fields.Char('Post Caption', compute='_compute_post_info', store=False)
    post_url = fields.Char('Post URL', compute='_compute_post_info', store=False)
    media_url = fields.Char('Media URL', compute='_compute_post_info', store=False)
    opportunity_id = fields.Many2one('crm.lead', string="Opportunity")

    @api.depends('post_id')
    def _compute_post_info(self):
        for rec in self:
            if rec.post_id:
                rec.post_caption = rec.post_id.caption or ''
                if rec.post_id.meta_platform == "instagram":
                    rec.post_url = f'https://www.instagram.com/p/{rec.post_id.post_id}/'
                else:
                    rec.post_url = f'https://www.facebook.com/p/{rec.post_id.post_id}/'
                rec.media_url = rec.post_id.media_url or ''
            else:
                rec.post_caption = ''
                rec.post_url = ''
                rec.media_url = ''

    def create_opportunity_wizard(self):
        existing_opportunities = False
        # partner = self.env['res.partner'].search([('phone', '=', self.customer_number)], limit=1)
        if self.partner_id:
            existing_opportunities = self.env['crm.lead'].search([('partner_id', '=', self.partner_id.id)])
        return {
            'name': 'Convert to Opportunity',
            'type': 'ir.actions.act_window',
            'res_model': 'opportunity.convert.session.wizard',
            'view_mode': 'form',
            'context': {
                'default_comment_id': self.id,
                'default_conversion_action': 'merge' if existing_opportunities else 'convert',
                'default_user_id': self.env.user.id,
                'default_partner_action': 'exist' if self.partner_id else 'create',
                'default_partner_id': self.partner_id.id if self.partner_id.id else False,
                'default_opportunity_ids': existing_opportunities.ids if existing_opportunities else False,
            },
            'target': 'new',
        }


    # def send_reply_to_instagram(self):
    #     self.ensure_one()
    #     if not self.reply_text:
    #         raise UserError("Please enter a reply before sending.")
    #     provider = self.env['provider'].sudo().search([
    #         ('graph_api_authenticated', '=', True),
    #         ('meta_platform', '=', self.post_id.meta_platform)
    #     ], limit=1)
    #     token = provider.graph_api_token
    #     warning_message= f"No authenticated {self.post_id.meta_platform} provider found."
    #     if not provider:
    #         raise UserError(warning_message)
    #     url = f'https://graph.facebook.com/v24.0/{self.comment_id}/replies'
    #     if self.post_id.meta_platform == "instagram":
    #         url = f'https://graph.instagram.com/v24.0/{self.comment_id}/replies'
    #     else:
    #         url = f'https://graph.facebook.com/v24.0/{self.comment_id}/comments'
    #         token = provider.facebook_page_token
    #     data = {
    #         'message': self.reply_text,
    #         'access_token': token
    #     }
    #
    #     import requests
    #     try:
    #         response = requests.post(url, data=data, timeout=60)
    #         response.raise_for_status()
    #         data = response.json()
    #         return {
    #             'effect': {
    #                 'fadeout': 'slow',
    #                 'message': 'Reply sent successfully ✅',
    #                 'type': 'rainbow_man',
    #             }
    #         }
    #     except requests.exceptions.RequestException as e:
    #         raise UserError(f"Failed to send reply: {e}")

    def send_reply_to_instagram(self):
        self.ensure_one()
        if not self.reply_text:
            raise UserError("Please enter a reply before sending.")

        provider = self.env['provider'].sudo().search([
            ('graph_api_authenticated', '=', True),
            ('meta_platform', '=', self.post_id.meta_platform)
        ], limit=1)

        if not provider:
            warning_message = f"No authenticated {self.post_id.meta_platform} provider found."
            raise UserError(warning_message)

        token = provider.graph_api_token

        if self.post_id.meta_platform == "instagram":
            url = f'https://graph.instagram.com/v21.0/{self.comment_id}/replies'
            data = {
                'message': self.reply_text,
                'access_token': token
            }
        else:
            url = f'https://graph.facebook.com/v21.0/{self.comment_id}/comments'
            token = provider.facebook_page_token
            data = {
                'message': self.reply_text,
                'access_token': token
            }

        import requests
        try:
            response = requests.post(url, data=data, timeout=60)

            # If error, get the real reason from Instagram
            if response.status_code != 200:
                try:
                    error_info = response.json()
                    error_msg = error_info.get('error', {}).get('message', response.text)
                except:
                    error_msg = response.text
                raise UserError(f"Instagram API Error: {error_msg}")

            result = response.json()
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Reply sent successfully ✅',
                    'type': 'rainbow_man',
                }
            }
        except UserError:
            raise
        except requests.exceptions.RequestException as e:
            error_detail = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json().get('error', {}).get('message', e.response.text)
                except:
                    error_detail = e.response.text
            raise UserError(f"Failed to send reply: {error_detail or str(e)}")


class InstagramAccount(models.Model):
    _name = 'instagram.account'
    _description = 'Instagram Account'

    name = fields.Char('Account Name')
    account_id = fields.Char('Instagram User ID', required=True)
    access_token = fields.Char('Access Token', required=True)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    comment_id = fields.Many2one('post.comments', string='Comment ID')
