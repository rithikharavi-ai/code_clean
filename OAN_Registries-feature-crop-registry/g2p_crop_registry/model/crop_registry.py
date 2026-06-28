from odoo import api, fields, models
import re
from odoo.exceptions import ValidationError
from datetime import date
from odoo.addons.g2p_ati.models.utils import eth_date
import uuid

class G2PCrop(models.Model):
    _name = 'g2p.crop.registry'
    _description = 'G2p Crop Registry'

    # =======================================
    # UI Fields: Farmer Identity
    # =======================================
    partner_id = fields.Many2one('res.partner', string="Farmer ID", domain="[('is_farmer', '=', 'yes')]", required=True)
    fyda_id = fields.Char(string="Fayda ID", required=True)
    farmer_display_id = fields.Char(string='Farmer Name', required=True)
    region_name_id = fields.Many2one('g2p.region', string="Region",
                                     store=True
                                     )
    zone_name_id = fields.Many2one('g2p.zone',
                                   string='Zone',
                                   store=True
                                   )
    woreda_name_id = fields.Many2one('g2p.woreda',
                                     string='Woreda',
                                     store=True
                                     )
    kebele_id = fields.Many2one(
        'g2p.kebele',
        string='Kebele',
        domain="[('woreda', '=', woreda_name_id)]",
    )
    gps = fields.Char(string="GPS")

    # =======================================
    # UI Fields: Planning
    # =======================================
    seasonal_line_ids = fields.One2many(
        "g2p.seasonal.line",
        "crop_registry_id",
        string="Planned Input",
    )
    horticulture_line_ids = fields.One2many(
        "g2p.horticulture.line",
        "crop_registry_id",
        string="Horticulture Crops",
    )

    # =======================================
    # UI Fields: Cultivation / Land Preparation
    # =======================================
    actual_seasonal_line_ids = fields.One2many(
        "g2p.seasonal.actual.line",
        "crop_registry_id",
        string="Actual Input",
    )
    actual_horticulture_line_ids = fields.One2many(
        "g2p.horticulture.actual.line",
        "crop_registry_id",
        string="Horticulture Crops (Actual)",
    )

    # =======================================
    # UI Fields: Sowing
    # =======================================
    production_detail_ids = fields.One2many(
        "g2p.crop.production",
        "crop_registry_id",
        string="Sowing Details",
    )

    # =======================================
    # UI Fields: Harvesting
    # =======================================
    harvest_detail_ids = fields.One2many(
        related="production_detail_ids",
        readonly=False,
        string="Harvest Details",
    )

    # =======================================
    # UI Fields: Survey Personnel
    # =======================================
    surveyor_name = fields.Char(string="Surveyor Name")
    surveyor_mobile_number = fields.Char(string="Surveyor Mobile Number")
    supervisor_name = fields.Char(string="Supervisor Name")
    supervisor_mobile_number = fields.Char(string="Supervisor Mobile Number")
    first_approvel_status = fields.Selection([
        ('draft', 'Draft'),
    ], string="First approvel status")


    # =======================================
    # Unused / Deprecated Fields
    # =======================================
    land_info_id = fields.Many2one('g2p.land.information', string="Land ID")
    land_area = fields.Float(string="Total Land Area (ha)")
    # owner_name = fields.Char(string="Owner Name")
    ownership_type = fields.Selection([
        ('owner', 'Owner'),
        ('tenant', 'Tenant'),
        ('crop_share', 'Crop Sharing'),
        ('family_gift', 'Family Gift')
    ])
    soil_fertility = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ])
    crop_name_id = fields.Many2one('g2p.crop', string="Crop Name", compute="_compute_primary_crop_details", store=True)
    collected_gc = fields.Date(string="Planned Date (GC)")
    collected_ec = fields.Char(string="Planned Date (EC)")
    crop_category_id = fields.Many2one('g2p.crop.category', string="Crop Category", compute="_compute_primary_crop_details",
                                       store=True, readonly=True)
    crop_variety_id = fields.Many2one("g2p.crop.variety", string="Crop Variety", compute="_compute_primary_crop_details", store=True)
    crop_growth_duration = fields.Float(string="Average Growth Duration (days) ")
    crop_season_ids = fields.One2many(
        'g2p.crop.season.line',
        'crop_registry_id',
        string="Crop Seasons"
    )
    season_id = fields.Many2one("g2p.season", string="Season")
    start_gc = fields.Date(string="Start GC")
    end_gc = fields.Date(string="End GC")
    start_month = fields.Integer(string="Start Month", compute="_compute_start_date", store=True)
    start_day = fields.Integer(string="Start Day", compute="_compute_start_date", store=True)
    end_month = fields.Integer(string="End Month", compute="_compute_end_date", store=True)
    end_day = fields.Integer(string="End Day", compute="_compute_end_date", store=True)

    @api.onchange('season_id')
    def _onchange_season_id(self):
        if self.season_id:
            self.start_gc = self.season_id.start_gc
            self.end_gc = self.season_id.end_gc
            if self.season_id.start_gc:
                self.start_month = self.season_id.start_gc.month
                self.start_day = self.season_id.start_gc.day
            if self.season_id.end_gc:
                self.end_month = self.season_id.end_gc.month
                self.end_day = self.season_id.end_gc.day

    @api.depends("start_gc")
    def _compute_start_date(self):
        for record in self:
            if record.start_gc:
                record.start_month = record.start_gc.month
                record.start_day = record.start_gc.day
            else:
                record.start_month = record.start_day = 0

    @api.depends("end_gc")
    def _compute_end_date(self):
        for record in self:
            if record.end_gc:
                record.end_month = record.end_gc.month
                record.end_day = record.end_gc.day
            else:
                record.end_month = record.end_day = 0

    crop_planned_area = fields.Float(string="Planned Crop Area (ha)")
    land_prep_method_ids = fields.Many2many(
        "g2p.land.prep.method",
        string="Land Prep Method",
    )
    crop_expected = fields.Float(string="Expected Yield (quintals)")
    actual_yield = fields.Float(string="Actual Yield (ha)")
    cultivated_by = fields.Selection([
        ('tractor', 'Tractor'),
        ('other', 'Other'),
    ], string="Cultivation Type")

    # Actual Seasonal Crop fields (for Cultivation Details comparison)
    actual_crop_name_id = fields.Many2one('g2p.crop', string="Crop Name (Actual)")
    actual_collected_gc = fields.Date(string="Actual Planted Date (GC)")
    actual_collected_ec = fields.Char(string="Actual Planted Date (EC)")
    actual_crop_category_id = fields.Many2one(
        'g2p.crop.category', string="Crop Category (Actual)",
        compute="_compute_actual_crop_category", store=True, readonly=True
    )
    actual_crop_variety_id = fields.Many2one("g2p.crop.variety", string="Crop Variety (Actual)")

    actual_crop_growth_duration = fields.Float(string="Actual Growth Duration (days)")
    actual_crop_area = fields.Float(string="Actual Crop Area (ha)")

    # Mismatch computed fields for seasonal
    seasonal_crop_name_match = fields.Boolean(compute="_compute_seasonal_match", store=True)
    seasonal_date_gc_match = fields.Boolean(compute="_compute_seasonal_match", store=True)
    seasonal_variety_match = fields.Boolean(compute="_compute_seasonal_match", store=True)

    seed_planned = fields.Selection([('local', 'Local'),
                                     ('improved', 'Improved')], string="Seed Type")
    seed_planned_qty = fields.Float(string="Planned Seed Quantity (kg)")
    seed_planned_fertilizer_type = fields.Selection([
        ('organic', 'Organic Fertilizers (Natural & Soil-Friendly)'),
        ('nitrogen', 'Nitrogen Fertilizers (For Leaf Growth)'),
        ('phosphorus', 'Phosphorus Fertilizers (For Root & Flower Growth)'),
        ('potassium', 'Potassium Fertilizers (For Strength & Disease Resistance)'),
        ('npk', 'Complex / Mixed Fertilizers (NPK)'),
        ('micronutrient', 'Micronutrient Fertilizers (Small but Essential)'),
    ], string="Planned Fertilizer Type")
    seed_planned_fertilizer_name = fields.Many2one(
        'g2p.fertilizer',
        string="Planned Fertilizer Name",
        domain="[('category', '=', seed_planned_fertilizer_type)]"
    )
    seed_planned_fertilizer_qty = fields.Float(string="Planned Fertilizer Quantity (kg)")
    seed_planned_fertilizer_sack = fields.Float(
        string="Planned Fertilizer Sacks Count",
        compute="_compute_planned_fertilizer_sacks",
        store=True
    )
    water_resource_id = fields.Many2one('g2p.water.source', string="Main Water Resource")
    # main_water_source = fields.Selection([('rainfed', 'Rainfed'),
    #                                       ('surface_water', 'Surface Water'),
    #                                       ('irrigation', 'Irrigation')])
    # irrigation_method = fields.Char(string="Irrigation Type")
    # crop_produce_min = fields.Float(string="Crop Produce Min")
    # crop_produce_max = fields.Float(string="Crop Produce Max")
    # crop_wholesale_min = fields.Float(string="Crop Wholesale Min")
    # crop_wholesale_max = fields.Float(string="Crop Wholesale Max")
    # crop_retail_min = fields.Float(string="Crop Retail Min")
    # crop_retail_max = fields.Float(string="Crop Retail Max")
    # crop_volume = fields.Float(string="Crop Volume")
    # live_stock_type_id = fields.Many2one('g2p.livestock.type', string="Live Stock Type")
    # live_stock_number = fields.Integer(string="Live Stock Number")
    # live_stock_water_source = fields.Selection([
    #     ('river', 'River'),
    #     ('lake', 'Lake'),
    #     ('pond', 'Pond'),
    #     ('well', 'Well'),
    #     ('borewell', 'Borewell'),
    #     ('tap', 'Tap Water'),
    #     ('rainwater', 'Rain Water'),
    #     ('canal', 'Canal'),
    #     ('tank', 'Water Tank'),
    #     ('other', 'Other'),
    # ], string="Livestock Water Source")

    cultivation_land = fields.Boolean(string="Cultivation Land")
    cultivation_area = fields.Float(string="Cultivation Area")
    sown_land = fields.Boolean(string="Sown Land")
    sown_area = fields.Float(string="Sown Area")
    harvested_land = fields.Boolean(string="Harvested Land")
    harvested_area = fields.Float(string="Harvested Area")
    land_category = fields.Selection([('seasonal', 'Seasonal Crop'), ('horticulture', 'Horticulture Crop')], string="Plot Category")
    water_resource_line_ids = fields.One2many(
        "g2p.water.resource.line",
        "crop_registry_id",
        string="Water Resources",
    )
    actual_water_resource_line_ids = fields.One2many(
        "g2p.actual.water.resource.line",
        "crop_registry_id",
        string="Actual Water Resources",
    )
    production_plan = fields.Float(string="Production Plan")
    productivity = fields.Float(string="Productivity")
    total_cultivated_land = fields.Float(string="Total Cultivated Land")
    cultivated_land_by_tractor = fields.Float(string="Cultivated Land by Tractor")
    total_sown_land = fields.Float(string="Total Sown Land")
    sown_land_by_tractor = fields.Float(string="Sown Land by Tractor")
    # Farmers fields moved to planned lines

    production_in_quintal = fields.Float(string="Production in Quintal")
    total_plan = fields.Float(string="Total Plan")

    actual_seed_class = fields.Selection([('local', 'Local'),
                                          ('improved', 'Improved')], string="Seed Type")
    actual_seed_qty = fields.Float(string="Actual Seed Quantity (kg)")
    actual_fertilizer_type = fields.Selection([
        ('organic', 'Organic Fertilizers (Natural & Soil-Friendly)'),
        ('nitrogen', 'Nitrogen Fertilizers (For Leaf Growth)'),
        ('phosphorus', 'Phosphorus Fertilizers (For Root & Flower Growth)'),
        ('potassium', 'Potassium Fertilizers (For Strength & Disease Resistance)'),
        ('npk', 'Complex / Mixed Fertilizers (NPK)'),
        ('micronutrient', 'Micronutrient Fertilizers (Small but Essential)'),
    ], string="Actual Fertilizer Type")
    actual_fertilizer_name = fields.Many2one(
        'g2p.fertilizer',
        string="Actual Fertilizer Name",
        domain="[('category', '=', actual_fertilizer_type)]"
    )
    actual_fertilizer_qty = fields.Float(string="Actual Fertilizer Quantity (kg)")
    actual_fertilizer_sack = fields.Float(
        string="Actual Fertilizer Sacks Count",
        compute="_compute_actual_fertilizer_sacks",
        store=True
    )
    pest_occurrence = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Pest Occurrence")
    pest_line_ids = fields.One2many('g2p.crop.pest.line', 'crop_registry_id', string="Pest Details")
    
    weed_occurrence = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Weed Occurrence")
    weed_line_ids = fields.One2many('g2p.crop.weed.line', 'crop_registry_id', string="Weed Details")
    
    water_resource_name = fields.Char(related="water_resource_id.name", string="Water Resource Name")
    irrigation_method = fields.Char(string="Method ")
    irrigation_frequency = fields.Char(string="Frequency ")



    # =======================================
    # Commented Code
    # =======================================

    @api.constrains('surveyor_mobile_number', 'supervisor_mobile_number')
    def _check_mobile_numbers(self):
        for rec in self:
            for field in ['surveyor_mobile_number', 'supervisor_mobile_number']:
                number = rec[field]
                if number:
                    if not re.match(r'^(\+251[79]\d{8}|0[79]\d{8})$', number):
                        raise ValidationError("Please enter a valid mobile number")

    @api.constrains('seasonal_line_ids')
    def _check_planned_crop_area(self):
        pass # land_area has been moved from the parent record to the lines

    @api.model
    def create(self, vals):
        record = super(G2PCrop, self).create(vals)
        record._sync_crop_information()
        return record

    def action_add_another(self):
        self.ensure_one()
        # Create a new record with the same farmer and land info but empty crop/season details
        new_record = self.copy(default={
            'season_id': False,
            'crop_name_id': False,
            'collected_gc': False,
            'collected_ec': False,
            'crop_variety_id': False,
            'crop_planned_area': 0.0,
            'crop_growth_duration': 0.0,
            'crop_expected': 0.0,
            'seed_planned': False,
            'seed_planned_qty': 0.0,
            'seed_planned_fertilizer_type': False,
            'seed_planned_fertilizer_name': False,
            'seed_planned_fertilizer_qty': 0.0,
            'seed_planned_fertilizer_sack': 0.0,
            'water_resource_line_ids': [(5, 0, 0)],
            'land_prep_method_ids': [(5, 0, 0)],

            'production_detail_ids': [(5, 0, 0)],
            'actual_horticulture_line_ids': [(5, 0, 0)],

        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crop Sown Registry',
            'res_model': 'g2p.crop.registry',
            'view_mode': 'form',
            'res_id': new_record.id,
            'target': 'current',
        }

    def write(self, vals):
        res = super(G2PCrop, self).write(vals)
        self._sync_crop_information()
        if 'partner_id' in vals:
            for rec in self:
                partner = rec.partner_id
                if partner:
                    pass
        return res

    def _sync_crop_information(self):
        for record in self:
            partner = record.partner_id
            
            if not partner:
                continue
                
            # Sync water resources to farmer profile directly
            for w in record.water_resource_line_ids:
                if w.water_resource_id:
                    partner.write({'crop_water_sources': [(4, w.water_resource_id.id)]})
            for w in record.actual_water_resource_line_ids:
                if w.water_resource_id:
                    partner.write({'crop_water_sources': [(4, w.water_resource_id.id)]})

            season_id = record.season_id.id if record.season_id else False
            
            def _sync_water_lines(crop_info):
                crop_info.water_resource_line_ids.unlink()
                
                # Sync planned water resources
                for w in record.water_resource_line_ids:
                    self.env['g2p.crop.information.water.line'].create({
                        'crop_information_id': crop_info.id,
                        'water_resource_id': w.water_resource_id.id,
                        'method_id': w.method_id.id,
                        'frequency': w.frequency,
                    })
                
                # Sync actual water resources
                for w in record.actual_water_resource_line_ids:
                    self.env['g2p.crop.information.water.line'].create({
                        'crop_information_id': crop_info.id,
                        'water_resource_id': w.water_resource_id.id,
                        'method_id': w.method_id.id,
                        'frequency': w.frequency,
                    })

            if record.actual_seasonal_line_ids:
                for s_line in record.actual_seasonal_line_ids:
                    if not s_line.crop_name_id:
                        continue
                    existing = self.env['g2p.crop.information'].search([
                        ('partner_id', '=', partner.id),
                        ('crop', '=', s_line.crop_name_id.id),
                        ('collected_gc', '=', s_line.collected_gc),
                    ], limit=1)
                    
                    vals = {
                        'partner_id': partner.id,
                        'crop': s_line.crop_name_id.id,
                        'collected_gc': s_line.collected_gc,
                        'collected_ec': s_line.collected_ec,
                        'season': season_id,
                    }
                    if existing:
                        existing.write(vals)
                        _sync_water_lines(existing)
                    else:
                        new_info = self.env['g2p.crop.information'].create(vals)
                        _sync_water_lines(new_info)
                    
            elif record.actual_horticulture_line_ids:
                for h_line in record.actual_horticulture_line_ids:
                    if not h_line.crop_name_id:
                        continue
                    existing = self.env['g2p.crop.information'].search([
                        ('partner_id', '=', partner.id),
                        ('crop', '=', h_line.crop_name_id.id),
                        ('collected_gc', '=', h_line.collected_gc),
                    ], limit=1)
                    
                    vals = {
                        'partner_id': partner.id,
                        'crop': h_line.crop_name_id.id,
                        'collected_gc': h_line.collected_gc,
                        'collected_ec': h_line.collected_ec,
                        'season': season_id,
                    }
                    if existing:
                        existing.write(vals)
                        _sync_water_lines(existing)
                    else:
                        new_info = self.env['g2p.crop.information'].create(vals)
                        _sync_water_lines(new_info)

    @api.onchange('partner_id')
    def _onchange_partner_id_details(self):
        if self.partner_id:
            farmer = self.partner_id
            if farmer:
                self.farmer_display_id = farmer.name
                self.region_name_id = farmer.region.id if hasattr(farmer, 'region') and farmer.region else False
                self.zone_name_id = farmer.zone.id if hasattr(farmer, 'zone') and farmer.zone else False
                self.woreda_name_id = farmer.woreda.id if hasattr(farmer, 'woreda') and farmer.woreda else False
                self.kebele_id = farmer.kebele.id if hasattr(farmer, 'kebele') and farmer.kebele else False
                
                if hasattr(farmer, 'partner_latitude') and hasattr(farmer, 'partner_longitude'):
                    if farmer.partner_latitude and farmer.partner_longitude:
                        self.gps = f"{farmer.partner_latitude}, {farmer.partner_longitude}"
                
                # Fetch Fayda ID
                uid_type = self.env['g2p.id.type'].search([('name', '=', 'UID')], limit=1)
                if uid_type:
                    fayda = self.env['g2p.reg.id'].search([
                        ('partner_id', '=', farmer.id),
                        ('id_type', '=', uid_type.id)
                    ], limit=1)
                    if fayda:
                        self.fyda_id = fayda.value
                    else:
                        self.fyda_id = False
                else:
                    self.fyda_id = False

                return {'domain': {'land_info_id': [('partner_id', '=', farmer.id)]}}
            else:
                return {'domain': {'land_info_id': [('id', '=', False)]}}
        else:
            self.farmer_display_id = False
            self.fyda_id = False
            self.region_name_id = False
            self.zone_name_id = False
            self.woreda_name_id = False
            self.kebele_id = False
            self.gps = False
            return {'domain': {'land_info_id': [('id', '=', False)]}}

    @api.onchange('land_info_id')
    def _onchange_land_info_id(self):
        if self.land_info_id:
            self.land_area = self.land_info_id.total_land_area
            self.ownership_type = self.land_info_id.ownership_type
            if hasattr(self.land_info_id, 'soil_fertility') and self.land_info_id.soil_fertility:
                self.soil_fertility = self.land_info_id.soil_fertility.lower()
            if self.land_info_id.land_kebele:
                self.kebele_id = self.land_info_id.land_kebele.id
                if self.land_info_id.land_kebele.woreda:
                    self.woreda_name_id = self.land_info_id.land_kebele.woreda.id
                    if self.land_info_id.land_kebele.woreda.zone:
                        self.zone_name_id = self.land_info_id.land_kebele.woreda.zone.id
                        if self.land_info_id.land_kebele.woreda.zone.region:
                            self.region_name_id = self.land_info_id.land_kebele.woreda.zone.region.id
                        else:
                            self.region_name_id = False
                    else:
                        self.zone_name_id = False
                        self.region_name_id = False
                else:
                    self.woreda_name_id = False
                    self.zone_name_id = False
                    self.region_name_id = False
            else:
                self.kebele_id = False
                self.woreda_name_id = False
                self.zone_name_id = False
                self.region_name_id = False

            if hasattr(self.land_info_id, 'polygon_data') and self.land_info_id.polygon_data:
                self.gps = self.land_info_id.polygon_data
            else:
                self.gps = False
    @api.onchange('crop_name_id')
    def _onchange_crop_id(self):
        self.crop_variety_id = False
        return {'domain': {'crop_variety_id': [('crop_id', '=', self.crop_name_id.id)]}}

    # @api.onchange('crop_name_id')
    # def _onchange_crop_name_id(self):
    #     for rec in self:
    #         if rec.crop_name_id:
    #             rec.crop_category_id = rec.crop_name_id.category.id
    #         else:
    #             rec.crop_category_id = False

    @api.depends('seasonal_line_ids.crop_name_id', 'seasonal_line_ids.crop_variety_id',
                 'horticulture_line_ids.crop_name_id', 'horticulture_line_ids.crop_variety_id')
    def _compute_primary_crop_details(self):
        for rec in self:
            crop_name = False
            crop_variety = False
            if rec.seasonal_line_ids:
                first_line = rec.seasonal_line_ids[0]
                crop_name = first_line.crop_name_id
                crop_variety = first_line.crop_variety_id
            elif rec.horticulture_line_ids:
                first_line = rec.horticulture_line_ids[0]
                crop_name = first_line.crop_name_id
                crop_variety = first_line.crop_variety_id
                
            rec.crop_name_id = crop_name.id if crop_name else False
            rec.crop_category_id = crop_name.category.id if crop_name and crop_name.category else False
            rec.crop_variety_id = crop_variety.id if crop_variety else False

    @api.depends('actual_crop_name_id')
    def _compute_actual_crop_category(self):
        for rec in self:
            rec.actual_crop_category_id = (
                rec.actual_crop_name_id.category.id
                if rec.actual_crop_name_id else False
            )

    @api.depends('crop_name_id', 'actual_crop_name_id',
                 'collected_gc', 'actual_collected_gc',
                 'crop_variety_id', 'actual_crop_variety_id')
    def _compute_seasonal_match(self):
        for rec in self:
            rec.seasonal_crop_name_match = (
                rec.actual_crop_name_id and
                rec.actual_crop_name_id.id == rec.crop_name_id.id
            )
            rec.seasonal_date_gc_match = (
                rec.actual_collected_gc and
                rec.actual_collected_gc == rec.collected_gc
            )
            rec.seasonal_variety_match = (
                rec.actual_crop_variety_id and
                rec.actual_crop_variety_id.id == rec.crop_variety_id.id
            )

    @api.constrains('fyda_id')
    def _check_ids(self):
        for rec in self:

            # Fayda ID validation -> FAN- + 16 digits
            if rec.fyda_id:
                fyda_pattern = r'^FAN-\d{16}$'
                if not re.match(fyda_pattern, rec.fyda_id):
                    raise ValidationError(
                        "Fayda ID must be in this format: FAN-1234567890123456"
                    )

    @api.onchange("collected_gc", "start_gc", "end_gc")
    def _onchange_collected_gc(self):
        if self.collected_gc:
            if self.start_gc and self.end_gc:
                if self.collected_gc < self.start_gc or self.collected_gc > self.end_gc:
                    self.collected_gc = False
                    self.collected_ec = False
                    return {
                        'warning': {
                            'title': 'Invalid Planned Date',
                            'message': 'Planned Date (GC) must be within the Season Details (Start GC and End GC).'
                        }
                    }

            cdate = date(
                self.collected_gc.year,
                self.collected_gc.month,
                self.collected_gc.day,
            )
            ethiopian_date = eth_date.to_ethiopian(
                cdate.year, cdate.month, cdate.day
            )
            self.collected_ec = eth_date.convert_tuple_to_string_with_separator(
                ethiopian_date
            )

    @api.onchange("collected_ec")
    def _onchange_collected_ec(self):
        if self.collected_ec:
            eth_date.check_ethipian_date_str(self.collected_ec, future_date=True)
            date_list = re.split("[-/,]", self.collected_ec)
            gc_date = eth_date.to_gregorian(
                int(date_list[2]), int(date_list[1]), int(date_list[0])
            )
            self.collected_gc = gc_date

    @api.onchange("actual_collected_gc")
    def _onchange_actual_collected_gc(self):
        if self.actual_collected_gc:
            cdate = date(
                self.actual_collected_gc.year,
                self.actual_collected_gc.month,
                self.actual_collected_gc.day,
            )
            ethiopian_date = eth_date.to_ethiopian(
                cdate.year, cdate.month, cdate.day
            )
            self.actual_collected_ec = eth_date.convert_tuple_to_string_with_separator(
                ethiopian_date
            )

    @api.onchange('actual_fertilizer_type')
    def _onchange_actual_fertilizer_type(self):
        self.actual_fertilizer_name = False
        return {'domain': {'actual_fertilizer_name': [('category', '=', self.actual_fertilizer_type)]}}

    @api.depends('actual_fertilizer_qty')
    def _compute_actual_fertilizer_sacks(self):
        for rec in self:
            if rec.actual_fertilizer_qty:
                rec.actual_fertilizer_sack = rec.actual_fertilizer_qty / 50
            else:
                rec.actual_fertilizer_sack = 0

    @api.onchange('actual_fertilizer_qty')
    def _onchange_actual_fertilizer_qty(self):
        for rec in self:
            if rec.actual_fertilizer_qty:
                rec.actual_fertilizer_sack = rec.actual_fertilizer_qty / 50
            else:
                rec.actual_fertilizer_sack = 0

    @api.onchange('seasonal_line_ids')
    def _onchange_sync_seasonal_lines(self):
        for rec in self:
            for planned_line in rec.seasonal_line_ids:
                if not planned_line.season_id or not planned_line.crop_name_id:
                    continue
                
                if not planned_line.sync_id:
                    planned_line.sync_id = str(uuid.uuid4())
                
                # Sync Actual Lines
                existing_actual = rec.actual_seasonal_line_ids.filtered(
                    lambda l: l.sync_id == planned_line.sync_id or (not l.sync_id and l.season_id == planned_line.season_id and l.crop_name_id == planned_line.crop_name_id)
                )
                if not existing_actual:
                    new_line = self.env['g2p.seasonal.actual.line'].new({
                        'sync_id': planned_line.sync_id,
                        'land_info_id': planned_line.land_info_id.id if planned_line.land_info_id else False,
                        'region_name_id': planned_line.region_name_id.id if planned_line.region_name_id else False,
                        'zone_name_id': planned_line.zone_name_id.id if planned_line.zone_name_id else False,
                        'woreda_name_id': planned_line.woreda_name_id.id if planned_line.woreda_name_id else False,
                        'kebele_id': planned_line.kebele_id.id if planned_line.kebele_id else False,
                        'gps': planned_line.gps,
                        'ownership_type': planned_line.ownership_type,
                        'land_area': planned_line.land_area,
                        'soil_fertility': planned_line.soil_fertility,
                        'land_category': planned_line.land_category if planned_line.land_category else False,
                        'season_id': planned_line.season_id.id,
                        'start_gc': planned_line.start_gc,
                        'end_gc': planned_line.end_gc,
                        'crop_name_id': planned_line.crop_name_id.id,
                        'crop_category_id': planned_line.crop_category_id.id if planned_line.crop_category_id else False,
                        'crop_variety_id': planned_line.crop_variety_id.id if planned_line.crop_variety_id else False,
                        'actual_crop_area': planned_line.crop_planned_area,
                        'actual_growth_duration': planned_line.crop_growth_duration,
                        'actual_seed_class': planned_line.seed_planned if planned_line.seed_planned else False,
                        'actual_seed_qty': planned_line.seed_planned_qty,
                        'actual_fertilizer_type': planned_line.seed_planned_fertilizer_type if planned_line.seed_planned_fertilizer_type else False,
                        'actual_fertilizer_name': planned_line.seed_planned_fertilizer_name if planned_line.seed_planned_fertilizer_name else False,
                        'actual_fertilizer_qty': planned_line.seed_planned_fertilizer_qty,
                        'collected_gc': planned_line.collected_gc,
                        'collected_ec': planned_line.collected_ec,
                        'has_cluster_farming': planned_line.has_cluster_farming if planned_line.has_cluster_farming else False,
                        'actual_cluster_plan': planned_line.cluster_plan if planned_line.cluster_plan else 0.0,
                        'actual_cluster_collected_land': planned_line.cluster_collected_land if planned_line.cluster_collected_land else 0.0,
                        'actual_cluster_collected_quintal': planned_line.cluster_collected_quintal if planned_line.cluster_collected_quintal else 0.0,
                        'actual_cluster_participant_farmers': planned_line.cluster_participant_farmers if planned_line.cluster_participant_farmers else 0,
                        'actual_collected_land': planned_line.collected_land if planned_line.collected_land else 0.0,
                        'actual_collected_land_quintal': planned_line.collected_land_quintal if planned_line.collected_land_quintal else 0.0,
                        'actual_collected_by_combiner': planned_line.collected_by_combiner if planned_line.collected_by_combiner else 0.0,
                        'water_resource_line_ids': [(0, 0, {
                            'water_resource_id': w.water_resource_id.id,
                            'method_id': w.method_id,
                            'frequency': w.frequency,
                        }) for w in planned_line.water_resource_line_ids],
                    })
                    rec.actual_seasonal_line_ids += new_line
                else:
                    for actual in existing_actual:
                        if not actual.sync_id:
                            actual.sync_id = planned_line.sync_id
                        if planned_line.crop_name_id and actual.crop_name_id != planned_line.crop_name_id:
                            actual.crop_name_id = planned_line.crop_name_id.id
                        if planned_line.land_info_id and actual.land_info_id != planned_line.land_info_id:
                            actual.land_info_id = planned_line.land_info_id.id
                        if planned_line.region_name_id and actual.region_name_id != planned_line.region_name_id:
                            actual.region_name_id = planned_line.region_name_id.id
                        if planned_line.zone_name_id and actual.zone_name_id != planned_line.zone_name_id:
                            actual.zone_name_id = planned_line.zone_name_id.id
                        if planned_line.woreda_name_id and actual.woreda_name_id != planned_line.woreda_name_id:
                            actual.woreda_name_id = planned_line.woreda_name_id.id
                        if planned_line.kebele_id and actual.kebele_id != planned_line.kebele_id:
                            actual.kebele_id = planned_line.kebele_id.id
                        if planned_line.gps and actual.gps != planned_line.gps:
                            actual.gps = planned_line.gps
                        if planned_line.ownership_type and actual.ownership_type != planned_line.ownership_type:
                            actual.ownership_type = planned_line.ownership_type
                        if planned_line.land_area and actual.land_area != planned_line.land_area:
                            actual.land_area = planned_line.land_area
                        if planned_line.soil_fertility and actual.soil_fertility != planned_line.soil_fertility:
                            actual.soil_fertility = planned_line.soil_fertility
                        if planned_line.land_category and actual.land_category != planned_line.land_category:
                            actual.land_category = planned_line.land_category
                        if planned_line.start_gc and actual.start_gc != planned_line.start_gc:
                            actual.start_gc = planned_line.start_gc
                        if planned_line.end_gc and actual.end_gc != planned_line.end_gc:
                            actual.end_gc = planned_line.end_gc
                        if planned_line.crop_planned_area and actual.actual_crop_area != planned_line.crop_planned_area:
                            actual.actual_crop_area = planned_line.crop_planned_area
                        if planned_line.crop_growth_duration and actual.actual_growth_duration != planned_line.crop_growth_duration:
                            actual.actual_growth_duration = planned_line.crop_growth_duration
                        if planned_line.seed_planned and actual.actual_seed_class != planned_line.seed_planned:
                            actual.actual_seed_class = planned_line.seed_planned
                        if planned_line.seed_planned_qty and actual.actual_seed_qty != planned_line.seed_planned_qty:
                            actual.actual_seed_qty = planned_line.seed_planned_qty
                        if planned_line.seed_planned_fertilizer_type and actual.actual_fertilizer_type != planned_line.seed_planned_fertilizer_type:
                            actual.actual_fertilizer_type = planned_line.seed_planned_fertilizer_type
                        if planned_line.seed_planned_fertilizer_name and actual.actual_fertilizer_name != planned_line.seed_planned_fertilizer_name:
                            actual.actual_fertilizer_name = planned_line.seed_planned_fertilizer_name
                        if planned_line.seed_planned_fertilizer_qty and actual.actual_fertilizer_qty != planned_line.seed_planned_fertilizer_qty:
                            actual.actual_fertilizer_qty = planned_line.seed_planned_fertilizer_qty
                        if planned_line.has_cluster_farming != actual.has_cluster_farming:
                            actual.has_cluster_farming = planned_line.has_cluster_farming
                        if planned_line.cluster_plan != actual.actual_cluster_plan:
                            actual.actual_cluster_plan = planned_line.cluster_plan
                        if planned_line.cluster_collected_land != actual.actual_cluster_collected_land:
                            actual.actual_cluster_collected_land = planned_line.cluster_collected_land
                        if planned_line.cluster_collected_quintal != actual.actual_cluster_collected_quintal:
                            actual.actual_cluster_collected_quintal = planned_line.cluster_collected_quintal
                        if planned_line.cluster_participant_farmers != actual.actual_cluster_participant_farmers:
                            actual.actual_cluster_participant_farmers = planned_line.cluster_participant_farmers
                        if planned_line.collected_land != actual.actual_collected_land:
                            actual.actual_collected_land = planned_line.collected_land
                        if planned_line.collected_land_quintal != actual.actual_collected_land_quintal:
                            actual.actual_collected_land_quintal = planned_line.collected_land_quintal
                        if planned_line.collected_by_combiner != actual.actual_collected_by_combiner:
                            actual.actual_collected_by_combiner = planned_line.collected_by_combiner
                        
                        planned_waters = {(w.water_resource_id.id, w.method_id, w.frequency) for w in planned_line.water_resource_line_ids}
                        actual_waters = {(w.water_resource_id.id, w.method_id, w.frequency) for w in actual.water_resource_line_ids}
                        if planned_waters != actual_waters:
                            actual.water_resource_line_ids = [(5, 0, 0)] + [(0, 0, {
                                'water_resource_id': w.water_resource_id.id,
                                'method_id': w.method_id,
                                'frequency': w.frequency,
                            }) for w in planned_line.water_resource_line_ids]
                
                # Sync Production Details
                existing_production = rec.production_detail_ids.filtered(
                    lambda p: p.sync_id == planned_line.sync_id or (not p.sync_id and p.season_id == planned_line.season_id and p.crop_name_id == planned_line.crop_name_id)
                )
                if not existing_production:
                    new_prod = self.env['g2p.crop.production'].new({
                        'sync_id': planned_line.sync_id,
                        'land_info_id': planned_line.land_info_id.id if planned_line.land_info_id else False,
                        'season_id': planned_line.season_id.id,
                        'crop_name_id': planned_line.crop_name_id.id,
                        'reg_seed_class': planned_line.seed_planned if planned_line.seed_planned else False,
                    })
                    rec.production_detail_ids += new_prod
                else:
                    for prod in existing_production:
                        if not prod.sync_id:
                            prod.sync_id = planned_line.sync_id
                        if planned_line.crop_name_id and prod.crop_name_id != planned_line.crop_name_id:
                            prod.crop_name_id = planned_line.crop_name_id.id
                        if planned_line.seed_planned and prod.reg_seed_class != planned_line.seed_planned:
                            prod.reg_seed_class = planned_line.seed_planned
                        if planned_line.land_info_id and prod.land_info_id != planned_line.land_info_id:
                            prod.land_info_id = planned_line.land_info_id.id
            
            # Cleanup orphaned seasonal actual lines
            planned_sync_ids = [l.sync_id for l in rec.seasonal_line_ids if l.sync_id]
            valid_sync_ids = planned_sync_ids + [l.sync_id for l in rec.horticulture_line_ids if l.sync_id]
            if True:
                orphaned_actual = rec.actual_seasonal_line_ids.filtered(lambda l: l.sync_id and l.sync_id not in planned_sync_ids)
                if orphaned_actual:
                    rec.actual_seasonal_line_ids -= orphaned_actual
                
                orphaned_prod = rec.production_detail_ids.filtered(lambda p: p.sync_id and p.sync_id not in valid_sync_ids)
                if orphaned_prod:
                    rec.production_detail_ids -= orphaned_prod
    

    @api.onchange('horticulture_line_ids')
    def _onchange_sync_horticulture_lines(self):
        for rec in self:
            for planned_line in rec.horticulture_line_ids:
                if not planned_line.season_id or not planned_line.crop_name_id:
                    continue
                
                if not planned_line.sync_id:
                    planned_line.sync_id = str(uuid.uuid4())
                
                # Sync Actual Lines
                existing_actual = rec.actual_horticulture_line_ids.filtered(
                    lambda l: l.sync_id == planned_line.sync_id or (not l.sync_id and l.season_id == planned_line.season_id and l.crop_name_id == planned_line.crop_name_id)
                )
                if not existing_actual:
                    new_line = self.env['g2p.horticulture.actual.line'].new({
                        'sync_id': planned_line.sync_id,
                        'land_info_id': planned_line.land_info_id.id if planned_line.land_info_id else False,
                        'region_name_id': planned_line.region_name_id.id if planned_line.region_name_id else False,
                        'zone_name_id': planned_line.zone_name_id.id if planned_line.zone_name_id else False,
                        'woreda_name_id': planned_line.woreda_name_id.id if planned_line.woreda_name_id else False,
                        'kebele_id': planned_line.kebele_id.id if planned_line.kebele_id else False,
                        'gps': planned_line.gps,
                        'land_category': planned_line.land_category if planned_line.land_category else False,
                        'season_id': planned_line.season_id.id,
                        'crop_name_id': planned_line.crop_name_id.id,
                        'crop_category_id': planned_line.crop_category_id.id if planned_line.crop_category_id else False,
                        'crop_variety_id': planned_line.crop_variety_id.id if planned_line.crop_variety_id else False,
                        'actual_crop_area': planned_line.crop_planned_area,
                        'actual_growth_duration': planned_line.crop_growth_duration,
                        'actual_seed_class': planned_line.seed_planned if planned_line.seed_planned else False,
                        'actual_seed_qty': planned_line.seed_planned_qty,
                        'actual_fertilizer_type': planned_line.seed_planned_fertilizer_type if planned_line.seed_planned_fertilizer_type else False,
                        'actual_fertilizer_name': planned_line.seed_planned_fertilizer_name if planned_line.seed_planned_fertilizer_name else False,
                        'actual_fertilizer_qty': planned_line.seed_planned_fertilizer_qty,
                        'collected_gc': planned_line.collected_gc,
                        'collected_ec': planned_line.collected_ec,
                        'has_cluster_farming': planned_line.has_cluster_farming if planned_line.has_cluster_farming else False,
                        'actual_cluster_plan': planned_line.cluster_plan if planned_line.cluster_plan else 0.0,
                        'actual_cluster_collected_land': planned_line.cluster_collected_land if planned_line.cluster_collected_land else 0.0,
                        'actual_cluster_collected_quintal': planned_line.cluster_collected_quintal if planned_line.cluster_collected_quintal else 0.0,
                        'actual_cluster_participant_farmers': planned_line.cluster_participant_farmers if planned_line.cluster_participant_farmers else 0,
                        'actual_collected_land': planned_line.collected_land if planned_line.collected_land else 0.0,
                        'actual_collected_land_quintal': planned_line.collected_land_quintal if planned_line.collected_land_quintal else 0.0,
                        'actual_collected_by_combiner': planned_line.collected_by_combiner if planned_line.collected_by_combiner else 0.0,
                        'water_resource_line_ids': [(0, 0, {
                            'water_resource_id': w.water_resource_id.id,
                            'method_id': w.method_id,
                            'frequency': w.frequency,
                        }) for w in planned_line.water_resource_line_ids],
                    })
                    rec.actual_horticulture_line_ids += new_line
                else:
                    for actual in existing_actual:
                        if not actual.sync_id:
                            actual.sync_id = planned_line.sync_id
                        if planned_line.crop_name_id and actual.crop_name_id != planned_line.crop_name_id:
                            actual.crop_name_id = planned_line.crop_name_id.id
                        if planned_line.seed_planned and actual.actual_seed_class != planned_line.seed_planned:
                            actual.actual_seed_class = planned_line.seed_planned
                        if planned_line.crop_planned_area and actual.actual_crop_area != planned_line.crop_planned_area:
                            actual.actual_crop_area = planned_line.crop_planned_area
                        if planned_line.crop_growth_duration and actual.actual_growth_duration != planned_line.crop_growth_duration:
                            actual.actual_growth_duration = planned_line.crop_growth_duration
                        if planned_line.seed_planned_qty and actual.actual_seed_qty != planned_line.seed_planned_qty:
                            actual.actual_seed_qty = planned_line.seed_planned_qty
                        if planned_line.seed_planned_fertilizer_type and actual.actual_fertilizer_type != planned_line.seed_planned_fertilizer_type:
                            actual.actual_fertilizer_type = planned_line.seed_planned_fertilizer_type
                        if planned_line.seed_planned_fertilizer_name and actual.actual_fertilizer_name != planned_line.seed_planned_fertilizer_name:
                            actual.actual_fertilizer_name = planned_line.seed_planned_fertilizer_name
                        if planned_line.seed_planned_fertilizer_qty and actual.actual_fertilizer_qty != planned_line.seed_planned_fertilizer_qty:
                            actual.actual_fertilizer_qty = planned_line.seed_planned_fertilizer_qty
                        if planned_line.land_info_id and actual.land_info_id != planned_line.land_info_id:
                            actual.land_info_id = planned_line.land_info_id.id
                        if planned_line.region_name_id and actual.region_name_id != planned_line.region_name_id:
                            actual.region_name_id = planned_line.region_name_id.id
                        if planned_line.zone_name_id and actual.zone_name_id != planned_line.zone_name_id:
                            actual.zone_name_id = planned_line.zone_name_id.id
                        if planned_line.woreda_name_id and actual.woreda_name_id != planned_line.woreda_name_id:
                            actual.woreda_name_id = planned_line.woreda_name_id.id
                        if planned_line.kebele_id and actual.kebele_id != planned_line.kebele_id:
                            actual.kebele_id = planned_line.kebele_id.id
                        if planned_line.gps and actual.gps != planned_line.gps:
                            actual.gps = planned_line.gps
                        if planned_line.land_category and actual.land_category != planned_line.land_category:
                            actual.land_category = planned_line.land_category
                        if planned_line.has_cluster_farming != actual.has_cluster_farming:
                            actual.has_cluster_farming = planned_line.has_cluster_farming
                        if planned_line.cluster_plan != actual.actual_cluster_plan:
                            actual.actual_cluster_plan = planned_line.cluster_plan
                        if planned_line.cluster_collected_land != actual.actual_cluster_collected_land:
                            actual.actual_cluster_collected_land = planned_line.cluster_collected_land
                        if planned_line.cluster_collected_quintal != actual.actual_cluster_collected_quintal:
                            actual.actual_cluster_collected_quintal = planned_line.cluster_collected_quintal
                        if planned_line.cluster_participant_farmers != actual.actual_cluster_participant_farmers:
                            actual.actual_cluster_participant_farmers = planned_line.cluster_participant_farmers
                        if planned_line.collected_land != actual.actual_collected_land:
                            actual.actual_collected_land = planned_line.collected_land
                        if planned_line.collected_land_quintal != actual.actual_collected_land_quintal:
                            actual.actual_collected_land_quintal = planned_line.collected_land_quintal
                        if planned_line.collected_by_combiner != actual.actual_collected_by_combiner:
                            actual.actual_collected_by_combiner = planned_line.collected_by_combiner

                        planned_waters = {(w.water_resource_id.id, w.method_id, w.frequency) for w in planned_line.water_resource_line_ids}
                        actual_waters = {(w.water_resource_id.id, w.method_id, w.frequency) for w in actual.water_resource_line_ids}
                        if planned_waters != actual_waters:
                            actual.water_resource_line_ids = [(5, 0, 0)] + [(0, 0, {
                                'water_resource_id': w.water_resource_id.id,
                                'method_id': w.method_id,
                                'frequency': w.frequency,
                            }) for w in planned_line.water_resource_line_ids]
                    
                # Sync Production Details
                existing_production = rec.production_detail_ids.filtered(
                    lambda p: p.sync_id == planned_line.sync_id or (not p.sync_id and p.season_id == planned_line.season_id and p.crop_name_id == planned_line.crop_name_id)
                )
                if not existing_production:
                    new_prod = self.env['g2p.crop.production'].new({
                        'sync_id': planned_line.sync_id,
                        'season_id': planned_line.season_id.id,
                        'crop_name_id': planned_line.crop_name_id.id,
                        'reg_seed_class': planned_line.seed_planned if planned_line.seed_planned else False,
                    })
                    rec.production_detail_ids += new_prod
                else:
                    for prod in existing_production:
                        if not prod.sync_id:
                            prod.sync_id = planned_line.sync_id
                        if planned_line.crop_name_id and prod.crop_name_id != planned_line.crop_name_id:
                            prod.crop_name_id = planned_line.crop_name_id.id
                        if planned_line.seed_planned and prod.reg_seed_class != planned_line.seed_planned:
                            prod.reg_seed_class = planned_line.seed_planned
                            
            # Cleanup orphaned horticulture actual lines
            planned_horti_sync_ids = [l.sync_id for l in rec.horticulture_line_ids if l.sync_id]
            valid_sync_ids = planned_horti_sync_ids + [l.sync_id for l in rec.seasonal_line_ids if l.sync_id]
            if True:
                orphaned_horti_actual = rec.actual_horticulture_line_ids.filtered(lambda l: l.sync_id and l.sync_id not in planned_horti_sync_ids)
                if orphaned_horti_actual:
                    rec.actual_horticulture_line_ids -= orphaned_horti_actual
                
                # Check for orphaned production lines
                orphaned_horti_prod = rec.production_detail_ids.filtered(lambda p: p.sync_id and p.sync_id not in valid_sync_ids)
                if orphaned_horti_prod:
                    rec.production_detail_ids -= orphaned_horti_prod

    @api.onchange('actual_seasonal_line_ids')
    def _onchange_sync_actual_to_production_seasonal(self):
        for rec in self:
            for actual_line in rec.actual_seasonal_line_ids:
                if not actual_line.sync_id: continue
                prod_line = rec.production_detail_ids.filtered(lambda p: p.sync_id == actual_line.sync_id)
                if prod_line:
                    # Assuming 1-to-1 mapping
                    prod_line = prod_line[0]
                    if prod_line.season_id != actual_line.season_id:
                        prod_line.season_id = actual_line.season_id
                    if prod_line.crop_name_id != actual_line.crop_name_id:
                        prod_line.crop_name_id = actual_line.crop_name_id
                    if prod_line.reg_seed_class != actual_line.actual_seed_class:
                        prod_line.reg_seed_class = actual_line.actual_seed_class
                    if prod_line.land_info_id != actual_line.land_info_id:
                        prod_line.land_info_id = actual_line.land_info_id.id
                else:
                    new_prod = self.env['g2p.crop.production'].new({
                        'sync_id': actual_line.sync_id,
                        'season_id': actual_line.season_id.id if actual_line.season_id else False,
                        'crop_name_id': actual_line.crop_name_id.id if actual_line.crop_name_id else False,
                        'reg_seed_class': actual_line.actual_seed_class if actual_line.actual_seed_class else False,
                        'land_info_id': actual_line.land_info_id.id if actual_line.land_info_id else False,
                    })
                    rec.production_detail_ids += new_prod

    @api.onchange('actual_horticulture_line_ids')
    def _onchange_sync_actual_to_production_horticulture(self):
        for rec in self:
            for actual_line in rec.actual_horticulture_line_ids:
                if not actual_line.sync_id: continue
                prod_line = rec.production_detail_ids.filtered(lambda p: p.sync_id == actual_line.sync_id)
                if prod_line:
                    prod_line = prod_line[0]
                    if prod_line.season_id != actual_line.season_id:
                        prod_line.season_id = actual_line.season_id
                    if prod_line.crop_name_id != actual_line.crop_name_id:
                        prod_line.crop_name_id = actual_line.crop_name_id
                    if prod_line.reg_seed_class != actual_line.actual_seed_class:
                        prod_line.reg_seed_class = actual_line.actual_seed_class
                    if prod_line.land_info_id != actual_line.land_info_id:
                        prod_line.land_info_id = actual_line.land_info_id.id
                else:
                    new_prod = self.env['g2p.crop.production'].new({
                        'sync_id': actual_line.sync_id,
                        'season_id': actual_line.season_id.id if actual_line.season_id else False,
                        'crop_name_id': actual_line.crop_name_id.id if actual_line.crop_name_id else False,
                        'reg_seed_class': actual_line.actual_seed_class if actual_line.actual_seed_class else False,
                        'land_info_id': actual_line.land_info_id.id if actual_line.land_info_id else False,
                    })
                    rec.production_detail_ids += new_prod

class G2PHorticultureLine(models.Model):
    _name = "g2p.horticulture.line"
    _description = "Horticulture Crop Planned Line"

    crop_registry_id = fields.Many2one("g2p.crop.registry", string="Crop Registry", ondelete="cascade")
    sync_id = fields.Char(string="Sync ID", default=lambda self: str(uuid.uuid4()))
    land_info_id = fields.Many2one('g2p.land.information', string="Land ID")
    region_name_id = fields.Many2one('g2p.region', string='Region')
    zone_name_id = fields.Many2one('g2p.zone', string='Zone')
    woreda_name_id = fields.Many2one('g2p.woreda', string='Woreda')
    kebele_id = fields.Many2one('g2p.kebele', string='Kebele')
    gps = fields.Char(string='GPS Coordinates')

    ownership_type = fields.Selection([('owner', 'Owner'), ('tenant', 'Tenant'), ('crop_share', 'Crop Sharing'), ('family_gift', 'Family Gift')], string="Ownership Type")
    land_area = fields.Float(string="Total Land Area (ha)")
    land_category = fields.Selection([('seasonal', 'Seasonal Crop'), ('horticulture', 'Horticulture Crop')], string="Plot Category")
    soil_fertility = fields.Char(string="Soil Fertility")
    season_id = fields.Many2one('g2p.season', string="Season", required=True)
    start_gc = fields.Date(string="Start GC")
    start_month = fields.Integer(string="Start Month", compute="_compute_start_date", store=True)
    start_day = fields.Integer(string="Start Day", compute="_compute_start_date", store=True)
    end_gc = fields.Date(string="End GC")
    end_month = fields.Integer(string="End Month", compute="_compute_end_date", store=True)
    end_day = fields.Integer(string="End Day", compute="_compute_end_date", store=True)
    
    crop_name_id = fields.Many2one("g2p.crop", string="Crop", required=True)
    collected_gc = fields.Date(string="Planned Date (GC)")
    collected_ec = fields.Char(string="Planned Date (EC)")
    crop_category_id = fields.Many2one("g2p.crop.category", string="Crop Category", compute="_compute_crop_category", store=True, readonly=True)
    crop_variety_id = fields.Many2one("g2p.crop.variety", string="Crop Variety")
    
    crop_planned_area = fields.Float(string="Planned Crop Area (ha)")

    @api.onchange('land_info_id')
    def _onchange_land_info_id(self):
        if self.land_info_id:
            self.land_area = self.land_info_id.total_land_area
            self.ownership_type = self.land_info_id.ownership_type
            if hasattr(self.land_info_id, 'soil_fertility') and self.land_info_id.soil_fertility:
                self.soil_fertility = self.land_info_id.soil_fertility.lower()
            if self.land_info_id.land_kebele:
                self.kebele_id = self.land_info_id.land_kebele.id
                if self.land_info_id.land_kebele.woreda:
                    self.woreda_name_id = self.land_info_id.land_kebele.woreda.id
                    if self.land_info_id.land_kebele.woreda.zone:
                        self.zone_name_id = self.land_info_id.land_kebele.woreda.zone.id
                        if self.land_info_id.land_kebele.woreda.zone.region:
                            self.region_name_id = self.land_info_id.land_kebele.woreda.zone.region.id
                        else:
                            self.region_name_id = False
                    else:
                        self.zone_name_id = False
                        self.region_name_id = False
                else:
                    self.woreda_name_id = False
                    self.zone_name_id = False
                    self.region_name_id = False
            else:
                self.kebele_id = False
                self.woreda_name_id = False
                self.zone_name_id = False
                self.region_name_id = False

            if hasattr(self.land_info_id, 'polygon_data') and self.land_info_id.polygon_data:
                self.gps = self.land_info_id.polygon_data
            else:
                self.gps = False
    crop_growth_duration = fields.Float(string="Average Growth Duration (days)")
    crop_expected = fields.Float(string="Expected Yield (quintals)")
    
    seed_planned = fields.Selection([('local', 'Local'), ('improved', 'Improved')], string="Seed Type")
    seed_planned_qty = fields.Float(string="Planned Seed Quantity (kg)")
    seed_planned_fertilizer_type = fields.Selection([
        ('organic', 'Organic'),
        ('inorganic', 'Inorganic'),
        ('biofertilizer', 'Bio Fertilizer')
    ], string="Planned Fertilizer Type")
    seed_planned_fertilizer_name = fields.Many2one('g2p.fertilizer', string="Planned Fertilizer Name", domain="[('category', '=', seed_planned_fertilizer_type)]")
    seed_planned_fertilizer_qty = fields.Float(string="Planned Fertilizer Quantity (kg)")
    seed_planned_fertilizer_sack = fields.Float(string="Planned Fertilizer Sacks Count", compute="_compute_planned_fertilizer_sacks", store=True)
    water_resource_line_ids = fields.One2many('g2p.water.resource.line', 'horticulture_line_id', string="Water Resources")
    
    # Actual Inputs Fields
    actual_season_id = fields.Many2one('g2p.season', string="Actual Season")
    actual_start_gc = fields.Date(string="Actual Start GC")
    actual_start_month = fields.Integer(string="Actual Start Month")
    actual_start_day = fields.Integer(string="Actual Start Day")
    actual_end_gc = fields.Date(string="Actual End GC")
    actual_end_month = fields.Integer(string="Actual End Month")
    actual_end_day = fields.Integer(string="Actual End Day")
    
    actual_crop_name_id = fields.Many2one("g2p.crop", string="Actual Crop")
    actual_collected_gc = fields.Date(string="Actual Date (GC)")
    actual_collected_ec = fields.Char(string="Actual Date (EC)")
    actual_crop_category_id = fields.Many2one("g2p.crop.category", string="Actual Crop Category", compute="_compute_actual_crop_category", store=True)
    actual_crop_variety_id = fields.Many2one("g2p.crop.variety", string="Actual Crop Variety")

    actual_crop_area = fields.Float(string="Actual Crop Area (ha)")
    actual_growth_duration = fields.Float(string="Actual Growth Duration (days)")
    
    actual_seed_class = fields.Selection([('local', 'Local'), ('improved', 'Improved')], string="Seed Type")
    actual_seed_qty = fields.Float(string="Actual Seed Quantity (kg)")
    actual_fertilizer_type = fields.Selection([
        ('organic', 'Organic'),
        ('inorganic', 'Inorganic'),
        ('biofertilizer', 'Bio Fertilizer')
    ], string="Actual Fertilizer Type")
    actual_fertilizer_name = fields.Many2one('g2p.fertilizer', string="Actual Fertilizer Name", domain="[('category', '=', actual_fertilizer_type)]")
    actual_fertilizer_qty = fields.Float(string="Actual Fertilizer Quantity (kg)")
    actual_fertilizer_sack = fields.Float(string="Actual Fertilizer Sacks Count", compute="_compute_actual_fertilizer_sacks", store=True)
    
    pest_occurrence = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Pest Occurrence")
    pest_line_ids = fields.One2many('g2p.crop.pest.line', 'horticulture_line_id', string="Pest Details")
    
    weed_occurrence = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Weed Occurrence")
    weed_line_ids = fields.One2many('g2p.crop.weed.line', 'horticulture_line_id', string="Weed Details")
    
    actual_yield = fields.Float(string="Actual Yield (ha)")
    cultivated_by = fields.Selection([
        ('tractor', 'Tractor'),
        ('other', 'Other'),
    ], string="Cultivation Type")
    land_prep_method_ids = fields.Many2many("g2p.land.prep.method", string="Land Prep Methods")
    
    actual_water_resource_line_ids = fields.One2many(
        "g2p.actual.water.resource.line",
        "horticulture_line_id",
        string="Actual Water Resources",
    )
    
    planned_labor = fields.Integer(string="Planned Labor")
    has_cluster_farming = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Have you done any cluster farming or related activities earlier?")
    cluster_plan = fields.Float(string="Cluster Plan")
    cluster_collected_land = fields.Float(string="Cluster Collected Land")
    cluster_collected_quintal = fields.Float(string="Cluster Collected Quintal")
    cluster_participant_farmers = fields.Integer(string="Cluster Participant Farmers")
    collected_land = fields.Float(string="Collected Land")
    collected_land_quintal = fields.Float(string="Collected Land Quintal")
    collected_by_combiner = fields.Float(string="Collected by Combiner")


    @api.depends('seed_planned_fertilizer_qty')
    def _compute_planned_fertilizer_sacks(self):
        for rec in self:
            if rec.seed_planned_fertilizer_qty:
                rec.seed_planned_fertilizer_sack = rec.seed_planned_fertilizer_qty / 50.0
            else:
                rec.seed_planned_fertilizer_sack = 0.0

    @api.onchange('seed_planned_fertilizer_qty')
    def _onchange_fertilizer_qty(self):
        for rec in self:
            if rec.seed_planned_fertilizer_qty:
                rec.seed_planned_fertilizer_sack = rec.seed_planned_fertilizer_qty / 50.0
            else:
                rec.seed_planned_fertilizer_sack = 0.0

    @api.depends('actual_fertilizer_qty')
    def _compute_actual_fertilizer_sacks(self):
        for rec in self:
            if rec.actual_fertilizer_qty:
                rec.actual_fertilizer_sack = rec.actual_fertilizer_qty / 50.0
            else:
                rec.actual_fertilizer_sack = 0.0

    @api.onchange('crop_planned_area')
    def _onchange_crop_planned_area(self):
        if self.crop_registry_id and self.crop_planned_area and self.land_info_id:
            same_land_lines = self.crop_registry_id.horticulture_line_ids.filtered(lambda l: l.land_info_id == self.land_info_id)
            total_planned = sum(same_land_lines.mapped('crop_planned_area'))
            max_area = self.land_info_id.total_land_area
            if total_planned > max_area:
                attempted_area = self.crop_planned_area
                allocated_area = total_planned - attempted_area
                remaining_area = max_area - allocated_area
                
                # If they already messed up other lines, don't let it go negative in the message
                if remaining_area < 0:
                    remaining_area = 0.0
                    
                self.crop_planned_area = 0.0
                return {
                    'warning': {
                        'title': "Area Exceeded",
                        'message': "You entered %.2f ha, but only %.2f ha is remaining out of the total %.2f ha (%.2f ha is already allocated to other crops)." % (attempted_area, remaining_area, max_area, allocated_area)
                    }
                }

    @api.onchange('seed_planned_fertilizer_type')
    def _onchange_seed_planned_fertilizer_type(self):
        self.seed_planned_fertilizer_name = False
        return {'domain': {'seed_planned_fertilizer_name': [('category', '=', self.seed_planned_fertilizer_type)]}}

    @api.onchange('season_id')
    def _onchange_season_id(self):
        if self.season_id:
            self.start_gc = self.season_id.start_gc
            self.end_gc = self.season_id.end_gc

    @api.depends("start_gc")
    def _compute_start_date(self):
        for record in self:
            if record.start_gc:
                record.start_month = record.start_gc.month
                record.start_day = record.start_gc.day
            else:
                record.start_month = record.start_day = 0

    @api.depends("end_gc")
    def _compute_end_date(self):
        for record in self:
            if record.end_gc:
                record.end_month = record.end_gc.month
                record.end_day = record.end_gc.day
            else:
                record.end_month = record.end_day = 0

    @api.depends("crop_name_id")
    def _compute_crop_category(self):
        for rec in self:
            if rec.crop_name_id:
                rec.crop_category_id = rec.crop_name_id.category.id
            else:
                rec.crop_category_id = False

    @api.depends("actual_crop_name_id")
    def _compute_actual_crop_category(self):
        for rec in self:
            if rec.actual_crop_name_id:
                rec.actual_crop_category_id = rec.actual_crop_name_id.category.id
            else:
                rec.actual_crop_category_id = False

    @api.onchange("crop_name_id")
    def _onchange_crop(self):
        self.crop_variety_id = False
        return {
            "domain": {
                "crop_variety_id": [
                    ("crop_id", "=", self.crop_name_id.id)
                ]
            }
        }

    @api.onchange("collected_gc", "start_gc", "end_gc")
    def _onchange_collected_gc(self):
        if self.collected_gc:
            if self.start_gc and self.end_gc:
                # Check if the date is within the season's start and end months/dates
                if self.collected_gc < self.start_gc or self.collected_gc > self.end_gc:
                    self.collected_gc = False
                    self.collected_ec = False
                    return {
                        'warning': {
                            'title': 'Invalid Planned Date',
                            'message': 'Planned Date (GC) must be within the Season Details (Start GC and End GC).'
                        }
                    }

            cdate = date(
                self.collected_gc.year,
                self.collected_gc.month,
                self.collected_gc.day,
            )
            ethiopian_date = eth_date.to_ethiopian(
                cdate.year, cdate.month, cdate.day
            )
            self.collected_ec = eth_date.convert_tuple_to_string_with_separator(
                ethiopian_date
            )

    @api.onchange("collected_ec")
    def _onchange_collected_ec(self):
        if self.collected_ec:
            eth_date.check_ethipian_date_str(self.collected_ec, future_date=True)
            date_list = re.split("[-/,]", self.collected_ec)
            gc_date = eth_date.to_gregorian(
                int(date_list[2]), int(date_list[1]), int(date_list[0])
            )
            self.collected_gc = gc_date


class G2PLandPrepMethod(models.Model):
    _name = "g2p.land.prep.method"
    _description = "Land Preparation Method"

    name = fields.Char(string="Method Name", required=True)


class G2PHorticultureActualLine(models.Model):
    _name = "g2p.horticulture.actual.line"
    _description = "Horticulture Crop Actual Line"


    crop_registry_id = fields.Many2one("g2p.crop.registry", string="Crop Registry", ondelete="cascade")
    sync_id = fields.Char(string="Sync ID", default=lambda self: str(uuid.uuid4()))
    land_info_id = fields.Many2one('g2p.land.information', string="Land ID")
    region_name_id = fields.Many2one('g2p.region', string='Region')
    zone_name_id = fields.Many2one('g2p.zone', string='Zone')
    woreda_name_id = fields.Many2one('g2p.woreda', string='Woreda')
    kebele_id = fields.Many2one('g2p.kebele', string='Kebele')
    gps = fields.Char(string='GPS Coordinates')

    ownership_type = fields.Selection([('owner', 'Owner'), ('tenant', 'Tenant'), ('crop_share', 'Crop Sharing'), ('family_gift', 'Family Gift')], string="Ownership Type")
    land_area = fields.Float(string="Total Land Area (ha)")
    land_category = fields.Selection([('seasonal', 'Seasonal Crop'), ('horticulture', 'Horticulture Crop')], string="Plot Category")
    soil_fertility = fields.Char(string="Soil Fertility")

    @api.onchange('land_info_id')
    def _onchange_land_info_id(self):
        if self.land_info_id:
            self.land_area = self.land_info_id.total_land_area
            self.ownership_type = self.land_info_id.ownership_type
            if hasattr(self.land_info_id, 'soil_fertility') and self.land_info_id.soil_fertility:
                self.soil_fertility = self.land_info_id.soil_fertility.lower()
            if self.land_info_id.land_kebele:
                self.kebele_id = self.land_info_id.land_kebele.id
                if self.land_info_id.land_kebele.woreda:
                    self.woreda_name_id = self.land_info_id.land_kebele.woreda.id
                    if self.land_info_id.land_kebele.woreda.zone:
                        self.zone_name_id = self.land_info_id.land_kebele.woreda.zone.id
                        if self.land_info_id.land_kebele.woreda.zone.region:
                            self.region_name_id = self.land_info_id.land_kebele.woreda.zone.region.id
                        else:
                            self.region_name_id = False
                    else:
                        self.zone_name_id = False
                        self.region_name_id = False
                else:
                    self.woreda_name_id = False
                    self.zone_name_id = False
                    self.region_name_id = False
            else:
                self.kebele_id = False
                self.woreda_name_id = False
                self.zone_name_id = False
                self.region_name_id = False

            if hasattr(self.land_info_id, 'polygon_data') and self.land_info_id.polygon_data:
                self.gps = self.land_info_id.polygon_data
            else:
                self.gps = False
                
            if self.crop_registry_id:
                planned_line = self.crop_registry_id.horticulture_line_ids.filtered(
                    lambda l: l.land_info_id.id == self.land_info_id.id
                )
                if planned_line:
                    planned_line = planned_line[0]
                    water_resources = []
                    for w in planned_line.water_resource_line_ids:
                        water_resources.append((0, 0, {
                            'water_resource_id': w.water_resource_id.id,
                            'method_id': w.method_id,
                            'frequency': w.frequency,
                            'crop_registry_id': self.crop_registry_id.id,
                        }))
                    if water_resources:
                        self.water_resource_line_ids = [(5, 0, 0)] + water_resources
    season_id = fields.Many2one('g2p.season', string="Season", required=True)
    crop_name_id = fields.Many2one("g2p.crop", string="Crop", required=True)
    collected_gc = fields.Date(string="Actual Planted Date (GC)")
    collected_ec = fields.Char(string="Actual Planted Date (EC)")
    crop_category_id = fields.Many2one("g2p.crop.category", string="Crop Category", compute="_compute_crop_category", store=True, readonly=True)
    crop_variety_id = fields.Many2one("g2p.crop.variety", string="Crop Variety")
    remark = fields.Char(string="Remark")
    actual_crop_area = fields.Float(string="Actual Crop Area (ha)")
    actual_growth_duration = fields.Float(string="Actual Growth Duration (days)")
    
    actual_seed_class = fields.Selection([('local', 'Local'), ('improved', 'Improved')], string="Seed Type")
    actual_seed_qty = fields.Float(string="Actual Seed Quantity (kg)")
    actual_fertilizer_type = fields.Selection([
        ('organic', 'Organic'),
        ('inorganic', 'Inorganic'),
        ('biofertilizer', 'Bio Fertilizer')
    ], string="Actual Fertilizer Type")
    actual_fertilizer_name = fields.Many2one('g2p.fertilizer', string="Actual Fertilizer Name", domain="[('category', '=', actual_fertilizer_type)]")
    actual_fertilizer_qty = fields.Float(string="Actual Fertilizer Quantity (kg)")
    actual_fertilizer_sack = fields.Float(string="Actual Fertilizer Sacks Count", compute="_compute_actual_fertilizer_sacks", store=True)

    has_cluster_farming = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Have you done any cluster farming or related activities earlier?")
    actual_cluster_plan = fields.Float(string="Actual Cluster Plan")
    actual_cluster_collected_land = fields.Float(string="Actual Cluster Collected Land")
    actual_cluster_collected_quintal = fields.Float(string="Actual Cluster Collected Quintal")
    actual_cluster_participant_farmers = fields.Integer(string="Actual Cluster Participant Farmers")
    actual_collected_land = fields.Float(string="Actual Collected Land")
    actual_collected_land_quintal = fields.Float(string="Actual Collected Land Quintal")
    actual_collected_by_combiner = fields.Float(string="Actual Collected by Combiner")
    
    pest_occurrence = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Pest Occurrence")
    pest_line_ids = fields.One2many('g2p.crop.pest.line', 'actual_horticulture_line_id', string="Pest Details")
    
    weed_occurrence = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Weed Occurrence")
    weed_line_ids = fields.One2many('g2p.crop.weed.line', 'actual_horticulture_line_id', string="Weed Details")
    
    actual_yield = fields.Float(string="Actual Yield (ha)")
    cultivated_by = fields.Selection([
        ('tractor', 'Tractor'),
        ('other', 'Other'),
    ], string="Cultivation Type")
    land_prep_method_ids = fields.Many2many("g2p.land.prep.method", string="Land Prep Methods")
    
    water_resource_line_ids = fields.One2many(
        "g2p.actual.water.resource.line",
        "actual_horticulture_line_id",
        string="Water Resources",
    )
    
    start_gc = fields.Date(string="Start GC")
    start_month = fields.Integer(string="Start Month", compute="_compute_start_date", store=True)
    start_day = fields.Integer(string="Start Day", compute="_compute_start_date", store=True)
    end_gc = fields.Date(string="End GC")
    end_month = fields.Integer(string="End Month", compute="_compute_end_date", store=True)
    end_day = fields.Integer(string="End Day", compute="_compute_end_date", store=True)
    
    is_mismatch = fields.Boolean(string="Mismatch", compute="_compute_is_mismatch", store=True)

    @api.onchange('actual_crop_area')
    def _onchange_actual_crop_area(self):
        if self.crop_registry_id and self.actual_crop_area and self.land_info_id:
            same_land_lines = self.crop_registry_id.actual_horticulture_line_ids.filtered(lambda l: l.land_info_id == self.land_info_id)
            total_actual = sum(same_land_lines.mapped('actual_crop_area'))
            max_area = self.land_info_id.total_land_area
            if total_actual > max_area:
                attempted_area = self.actual_crop_area
                allocated_area = total_actual - attempted_area
                remaining_area = max_area - allocated_area
                
                if remaining_area < 0:
                    remaining_area = 0.0
                    
                self.actual_crop_area = 0.0
                return {
                    'warning': {
                        'title': "Area Exceeded",
                        'message': "You entered %.2f ha, but only %.2f ha is remaining out of the total %.2f ha (%.2f ha is already allocated to other actual crops)." % (attempted_area, remaining_area, max_area, allocated_area)
                    }
                }

    @api.depends('actual_fertilizer_qty')
    def _compute_actual_fertilizer_sacks(self):
        for rec in self:
            if rec.actual_fertilizer_qty:
                rec.actual_fertilizer_sack = rec.actual_fertilizer_qty / 50.0
            else:
                rec.actual_fertilizer_sack = 0.0

    @api.onchange('actual_fertilizer_qty')
    def _onchange_fertilizer_qty(self):
        for rec in self:
            if rec.actual_fertilizer_qty:
                rec.actual_fertilizer_sack = rec.actual_fertilizer_qty / 50.0
            else:
                rec.actual_fertilizer_sack = 0.0

    @api.onchange('season_id')
    def _onchange_season_id(self):
        if self.season_id:
            self.start_gc = self.season_id.start_gc
            self.end_gc = self.season_id.end_gc
            if self.season_id.start_gc:
                self.start_month = self.season_id.start_gc.month
                self.start_day = self.season_id.start_gc.day
            if self.season_id.end_gc:
                self.end_month = self.season_id.end_gc.month
                self.end_day = self.season_id.end_gc.day

    @api.depends("start_gc")
    def _compute_start_date(self):
        for record in self:
            if record.start_gc:
                record.start_month = record.start_gc.month
                record.start_day = record.start_gc.day
            else:
                record.start_month = record.start_day = 0

    @api.depends("end_gc")
    def _compute_end_date(self):
        for record in self:
            if record.end_gc:
                record.end_month = record.end_gc.month
                record.end_day = record.end_gc.day
            else:
                record.end_month = record.end_day = 0

    @api.depends("crop_name_id")
    def _compute_crop_category(self):
        for rec in self:
            if rec.crop_name_id:
                rec.crop_category_id = rec.crop_name_id.category.id
            else:
                rec.crop_category_id = False

    @api.depends("crop_name_id", "crop_variety_id", "collected_gc", "season_id",
                 "crop_registry_id.horticulture_line_ids",
                 "crop_registry_id.horticulture_line_ids.crop_name_id",
                 "crop_registry_id.horticulture_line_ids.crop_variety_id",
                 "crop_registry_id.horticulture_line_ids.collected_gc",
                 "crop_registry_id.horticulture_line_ids.season_id")
    def _compute_is_mismatch(self):
        for rec in self:
            if not rec.crop_registry_id or not rec.crop_name_id:
                rec.is_mismatch = False
                continue
            planned_lines = rec.crop_registry_id.horticulture_line_ids
            matched = False
            for planned in planned_lines:
                if (planned.crop_name_id.id == rec.crop_name_id.id
                        and planned.crop_variety_id.id == rec.crop_variety_id.id
                        and planned.season_id.id == rec.season_id.id
                        and planned.collected_gc == rec.collected_gc):
                    matched = True
                    break
            rec.is_mismatch = not matched

    @api.depends("crop_name_id")
    def _compute_crop_category(self):
        for rec in self:
            rec.crop_category_id = (
                rec.crop_name_id.category.id
                if rec.crop_name_id
                else False
            )

    @api.onchange("crop_name_id")
    def _onchange_crop(self):
        self.crop_variety_id = False
        return {
            "domain": {
                "crop_variety_id": [
                    ("crop_id", "=", self.crop_name_id.id)
                ]
            }
        }

    @api.onchange("collected_gc")
    def _onchange_collected_gc(self):
        if self.collected_gc:
            if self.collected_gc > fields.Date.today():
                self.collected_gc = False
                return {
                    'warning': {
                        'title': 'Invalid Date',
                        'message': 'Actual Planted Date (GC) cannot be a future date.'
                    }
                }
            cdate = date(
                self.collected_gc.year,
                self.collected_gc.month,
                self.collected_gc.day,
            )
            ethiopian_date = eth_date.to_ethiopian(
                cdate.year, cdate.month, cdate.day
            )
            self.collected_ec = eth_date.convert_tuple_to_string_with_separator(
                ethiopian_date
            )

    @api.onchange("collected_ec")
    def _onchange_collected_ec(self):
        if self.collected_ec:
            eth_date.check_ethipian_date_str(self.collected_ec, future_date=True)
            date_list = re.split("[-/,]", self.collected_ec)
            gc_date = eth_date.to_gregorian(
                int(date_list[2]), int(date_list[1]), int(date_list[0])
            )
            self.collected_gc = gc_date

class G2PWaterResourceLine(models.Model):
    _name = "g2p.water.resource.line"
    _description = "Water Resource Details"
    _rec_name = "water_resource_id"

    crop_registry_id = fields.Many2one('g2p.crop.registry', ondelete="cascade")
    seasonal_line_id = fields.Many2one('g2p.seasonal.line', ondelete="cascade")
    horticulture_line_id = fields.Many2one('g2p.horticulture.line', ondelete="cascade")
    water_resource_id = fields.Many2one('g2p.water.source', string="Water Resource", required=True)
    method_id = fields.Char(string="Method")
    frequency = fields.Char(string="Frequency")

class G2PActualWaterResourceLine(models.Model):
    _name = "g2p.actual.water.resource.line"
    _description = "Actual Water Resource Details"

    crop_registry_id = fields.Many2one('g2p.crop.registry', ondelete="cascade")
    actual_seasonal_line_id = fields.Many2one('g2p.seasonal.actual.line', ondelete="cascade")
    seasonal_line_id = fields.Many2one('g2p.seasonal.line', ondelete="cascade")
    actual_horticulture_line_id = fields.Many2one('g2p.horticulture.actual.line', ondelete="cascade")
    horticulture_line_id = fields.Many2one('g2p.horticulture.line', ondelete="cascade")
    water_resource_id = fields.Many2one('g2p.water.source', string="Water Resource", required=True)
    method_id = fields.Char(string="Method")
    frequency = fields.Char(string="Frequency")

class G2PSeasonalLine(models.Model):
    _name = "g2p.seasonal.line"
    _description = "Seasonal Crop Planned Line"

    crop_registry_id = fields.Many2one("g2p.crop.registry", string="Crop Registry", ondelete="cascade")
    sync_id = fields.Char(string="Sync ID", default=lambda self: str(uuid.uuid4()))
    land_info_id = fields.Many2one('g2p.land.information', string="Land ID")
    region_name_id = fields.Many2one('g2p.region', string='Region')
    zone_name_id = fields.Many2one('g2p.zone', string='Zone')
    woreda_name_id = fields.Many2one('g2p.woreda', string='Woreda')
    kebele_id = fields.Many2one('g2p.kebele', string='Kebele')
    gps = fields.Char(string='GPS Coordinates')

    ownership_type = fields.Selection([('owner', 'Owner'), ('tenant', 'Tenant'), ('crop_share', 'Crop Sharing'), ('family_gift', 'Family Gift')], string="Ownership Type")
    land_area = fields.Float(string="Total Land Area (ha)")
    land_category = fields.Selection([('seasonal', 'Seasonal Crop'), ('horticulture', 'Horticulture Crop')], string="Plot Category")
    soil_fertility = fields.Char(string="Soil Fertility")
    season_id = fields.Many2one('g2p.season', string="Season", required=True)
    start_gc = fields.Date(string="Start GC")
    start_month = fields.Integer(string="Start Month", compute="_compute_start_date", store=True)
    start_day = fields.Integer(string="Start Day", compute="_compute_start_date", store=True)
    end_gc = fields.Date(string="End GC")
    end_month = fields.Integer(string="End Month", compute="_compute_end_date", store=True)
    end_day = fields.Integer(string="End Day", compute="_compute_end_date", store=True)
    
    crop_name_id = fields.Many2one("g2p.crop", string="Crop", required=True)
    collected_gc = fields.Date(string="Planned Date (GC)")
    collected_ec = fields.Char(string="Planned Date (EC)")
    crop_category_id = fields.Many2one("g2p.crop.category", string="Crop Category", compute="_compute_crop_category", store=True, readonly=True)
    crop_variety_id = fields.Many2one("g2p.crop.variety", string="Crop Variety")

    @api.onchange('land_info_id')
    def _onchange_land_info_id(self):
        if self.land_info_id:
            self.land_area = self.land_info_id.total_land_area
            self.ownership_type = self.land_info_id.ownership_type
            if hasattr(self.land_info_id, 'soil_fertility') and self.land_info_id.soil_fertility:
                self.soil_fertility = self.land_info_id.soil_fertility.lower()
            if self.land_info_id.land_kebele:
                self.kebele_id = self.land_info_id.land_kebele.id
                if self.land_info_id.land_kebele.woreda:
                    self.woreda_name_id = self.land_info_id.land_kebele.woreda.id
                    if self.land_info_id.land_kebele.woreda.zone:
                        self.zone_name_id = self.land_info_id.land_kebele.woreda.zone.id
                        if self.land_info_id.land_kebele.woreda.zone.region:
                            self.region_name_id = self.land_info_id.land_kebele.woreda.zone.region.id
                        else:
                            self.region_name_id = False
                    else:
                        self.zone_name_id = False
                        self.region_name_id = False
                else:
                    self.woreda_name_id = False
                    self.zone_name_id = False
                    self.region_name_id = False
            else:
                self.kebele_id = False
                self.woreda_name_id = False
                self.zone_name_id = False
                self.region_name_id = False

            if hasattr(self.land_info_id, 'polygon_data') and self.land_info_id.polygon_data:
                self.gps = self.land_info_id.polygon_data
            else:
                self.gps = False
    
    crop_planned_area = fields.Float(string="Planned Crop Area (ha)")
    crop_growth_duration = fields.Float(string="Average Growth Duration (days)")
    crop_expected = fields.Float(string="Expected Yield (quintals)")
    
    seed_planned = fields.Selection([('local', 'Local'), ('improved', 'Improved')], string="Seed Type")
    seed_planned_qty = fields.Float(string="Planned Seed Quantity (kg)")
    seed_planned_fertilizer_type = fields.Selection([
        ('organic', 'Organic'),
        ('inorganic', 'Inorganic'),
        ('biofertilizer', 'Bio Fertilizer')
    ], string="Planned Fertilizer Type")
    seed_planned_fertilizer_name = fields.Many2one('g2p.fertilizer', string="Planned Fertilizer Name", domain="[('category', '=', seed_planned_fertilizer_type)]")
    seed_planned_fertilizer_qty = fields.Float(string="Planned Fertilizer Quantity (kg)")
    seed_planned_fertilizer_sack = fields.Float(string="Planned Fertilizer Sacks Count", compute="_compute_planned_fertilizer_sacks", store=True)
    water_resource_line_ids = fields.One2many('g2p.water.resource.line', 'seasonal_line_id', string="Water Resources")

    # Actual Inputs Fields
    actual_season_id = fields.Many2one('g2p.season', string="Actual Season")
    actual_start_gc = fields.Date(string="Actual Start GC")
    actual_start_month = fields.Integer(string="Actual Start Month")
    actual_start_day = fields.Integer(string="Actual Start Day")
    actual_end_gc = fields.Date(string="Actual End GC")
    actual_end_month = fields.Integer(string="Actual End Month")
    actual_end_day = fields.Integer(string="Actual End Day")
    
    actual_crop_name_id = fields.Many2one("g2p.crop", string="Actual Crop")
    actual_collected_gc = fields.Date(string="Actual Date (GC)")
    actual_collected_ec = fields.Char(string="Actual Date (EC)")
    actual_crop_category_id = fields.Many2one("g2p.crop.category", string="Actual Crop Category", compute="_compute_actual_crop_category", store=True)
    actual_crop_variety_id = fields.Many2one("g2p.crop.variety", string="Actual Crop Variety")

    actual_crop_area = fields.Float(string="Actual Crop Area (ha)")
    actual_growth_duration = fields.Float(string="Actual Growth Duration (days)")
    
    actual_seed_class = fields.Selection([('local', 'Local'), ('improved', 'Improved')], string="Seed Type")
    actual_seed_qty = fields.Float(string="Actual Seed Quantity (kg)")
    actual_fertilizer_type = fields.Selection([
        ('organic', 'Organic'),
        ('inorganic', 'Inorganic'),
        ('biofertilizer', 'Bio Fertilizer')
    ], string="Actual Fertilizer Type")
    actual_fertilizer_name = fields.Many2one('g2p.fertilizer', string="Actual Fertilizer Name", domain="[('category', '=', actual_fertilizer_type)]")
    actual_fertilizer_qty = fields.Float(string="Actual Fertilizer Quantity (kg)")
    actual_fertilizer_sack = fields.Float(string="Actual Fertilizer Sacks Count", compute="_compute_actual_fertilizer_sacks", store=True)
    
    pest_occurrence = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Pest Occurrence")
    pest_line_ids = fields.One2many('g2p.crop.pest.line', 'seasonal_line_id', string="Pest Details")
    
    weed_occurrence = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Weed Occurrence")
    weed_line_ids = fields.One2many('g2p.crop.weed.line', 'seasonal_line_id', string="Weed Details")
    
    actual_yield = fields.Float(string="Actual Yield (ha)")
    cultivated_by = fields.Selection([
        ('tractor', 'Tractor'),
        ('other', 'Other'),
    ], string="Cultivation Type")
    land_prep_method_ids = fields.Many2many("g2p.land.prep.method", string="Land Prep Methods")
    
    actual_water_resource_line_ids = fields.One2many(
        "g2p.actual.water.resource.line",
        "seasonal_line_id",
        string="Actual Water Resources",
    )

    planned_labor = fields.Integer(string="Planned Labor")
    has_cluster_farming = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Have you done any cluster farming or related activities earlier?")
    cluster_plan = fields.Float(string="Cluster Plan")
    cluster_collected_land = fields.Float(string="Cluster Collected Land")
    cluster_collected_quintal = fields.Float(string="Cluster Collected Quintal")
    cluster_participant_farmers = fields.Integer(string="Cluster Participant Farmers")
    collected_land = fields.Float(string="Collected Land")
    collected_land_quintal = fields.Float(string="Collected Land Quintal")
    collected_by_combiner = fields.Float(string="Collected by Combiner")


    @api.depends('seed_planned_fertilizer_qty')
    def _compute_planned_fertilizer_sacks(self):
        for rec in self:
            if rec.seed_planned_fertilizer_qty:
                rec.seed_planned_fertilizer_sack = rec.seed_planned_fertilizer_qty / 50.0
            else:
                rec.seed_planned_fertilizer_sack = 0.0

    @api.onchange('seed_planned_fertilizer_qty')
    def _onchange_fertilizer_qty(self):
        for rec in self:
            if rec.seed_planned_fertilizer_qty:
                rec.seed_planned_fertilizer_sack = rec.seed_planned_fertilizer_qty / 50.0
            else:
                rec.seed_planned_fertilizer_sack = 0.0

    @api.depends('actual_fertilizer_qty')
    def _compute_actual_fertilizer_sacks(self):
        for rec in self:
            if rec.actual_fertilizer_qty:
                rec.actual_fertilizer_sack = rec.actual_fertilizer_qty / 50.0
            else:
                rec.actual_fertilizer_sack = 0.0

    @api.onchange('crop_planned_area')
    def _onchange_crop_planned_area(self):
        if self.crop_registry_id and self.crop_planned_area and self.land_info_id:
            same_land_lines = self.crop_registry_id.seasonal_line_ids.filtered(lambda l: l.land_info_id == self.land_info_id)
            total_planned = sum(same_land_lines.mapped('crop_planned_area'))
            max_area = self.land_info_id.total_land_area
            if total_planned > max_area:
                attempted_area = self.crop_planned_area
                allocated_area = total_planned - attempted_area
                remaining_area = max_area - allocated_area
                
                # If they already messed up other lines, don't let it go negative in the message
                if remaining_area < 0:
                    remaining_area = 0.0
                    
                self.crop_planned_area = 0.0
                return {
                    'warning': {
                        'title': "Area Exceeded",
                        'message': "You entered %.2f ha, but only %.2f ha is remaining out of the total %.2f ha (%.2f ha is already allocated to other crops)." % (attempted_area, remaining_area, max_area, allocated_area)
                    }
                }

    @api.onchange('seed_planned_fertilizer_type')
    def _onchange_seed_planned_fertilizer_type(self):
        self.seed_planned_fertilizer_name = False
        return {'domain': {'seed_planned_fertilizer_name': [('category', '=', self.seed_planned_fertilizer_type)]}}

    @api.onchange('season_id')
    def _onchange_season_id(self):
        if self.season_id:
            self.start_gc = self.season_id.start_gc
            self.end_gc = self.season_id.end_gc
            if self.season_id.start_gc:
                self.start_month = self.season_id.start_gc.month
                self.start_day = self.season_id.start_gc.day
            if self.season_id.end_gc:
                self.end_month = self.season_id.end_gc.month
                self.end_day = self.season_id.end_gc.day

    @api.depends("start_gc")
    def _compute_start_date(self):
        for record in self:
            if record.start_gc:
                record.start_month = record.start_gc.month
                record.start_day = record.start_gc.day
            else:
                record.start_month = record.start_day = 0

    @api.depends("end_gc")
    def _compute_end_date(self):
        for record in self:
            if record.end_gc:
                record.end_month = record.end_gc.month
                record.end_day = record.end_gc.day
            else:
                record.end_month = record.end_day = 0

    @api.depends("crop_name_id")
    def _compute_crop_category(self):
        for rec in self:
            if rec.crop_name_id:
                rec.crop_category_id = rec.crop_name_id.category.id
            else:
                rec.crop_category_id = False

    @api.depends("actual_crop_name_id")
    def _compute_actual_crop_category(self):
        for rec in self:
            if rec.actual_crop_name_id:
                rec.actual_crop_category_id = rec.actual_crop_name_id.category.id
            else:
                rec.actual_crop_category_id = False

    @api.onchange("crop_name_id")
    def _onchange_crop(self):
        self.crop_variety_id = False
        return {
            "domain": {
                "crop_variety_id": [
                    ("crop_id", "=", self.crop_name_id.id)
                ]
            }
        }

    @api.onchange("collected_gc", "start_gc", "end_gc")
    def _onchange_collected_gc(self):
        if self.collected_gc:
            if self.start_gc and self.end_gc:
                # Check if the date is within the season's start and end months/dates
                if self.collected_gc < self.start_gc or self.collected_gc > self.end_gc:
                    self.collected_gc = False
                    self.collected_ec = False
                    return {
                        'warning': {
                            'title': 'Invalid Planned Date',
                            'message': 'Planned Date (GC) must be within the Season Details (Start GC and End GC).'
                        }
                    }

            cdate = date(
                self.collected_gc.year,
                self.collected_gc.month,
                self.collected_gc.day,
            )
            ethiopian_date = eth_date.to_ethiopian(
                cdate.year, cdate.month, cdate.day
            )
            self.collected_ec = eth_date.convert_tuple_to_string_with_separator(
                ethiopian_date
            )

    @api.onchange("collected_ec")
    def _onchange_collected_ec(self):
        if self.collected_ec:
            eth_date.check_ethipian_date_str(self.collected_ec, future_date=True)
            date_list = re.split("[-/,]", self.collected_ec)
            gc_date = eth_date.to_gregorian(
                int(date_list[2]), int(date_list[1]), int(date_list[0])
            )
            self.collected_gc = gc_date

class G2PCropSeasonLine(models.Model):
    _name = "g2p.crop.season.line"
    _description = "Crop Season Line"

    crop_registry_id = fields.Many2one("g2p.crop.registry", string="Crop Registry", ondelete="cascade")
    season_id = fields.Many2one("g2p.season", string="Season", required=True)
    start_gc = fields.Date(string="Start GC")
    end_gc = fields.Date(string="End GC")
    start_month = fields.Integer(string="Start Month", compute="_compute_start_date", store=True)
    start_day = fields.Integer(string="Start Day", compute="_compute_start_date", store=True)
    end_month = fields.Integer(string="End Month", compute="_compute_end_date", store=True)
    end_day = fields.Integer(string="End Day", compute="_compute_end_date", store=True)

    @api.onchange('season_id')
    def _onchange_season_id(self):
        if self.season_id:
            self.start_gc = self.season_id.start_gc
            self.end_gc = self.season_id.end_gc

    @api.depends("start_gc")
    def _compute_start_date(self):
        for record in self:
            if record.start_gc:
                record.start_month = record.start_gc.month
                record.start_day = record.start_gc.day
            else:
                record.start_month = record.start_day = 0

    @api.depends("end_gc")
    def _compute_end_date(self):
        for record in self:
            if record.end_gc:
                record.end_month = record.end_gc.month
                record.end_day = record.end_gc.day
            else:
                record.end_month = record.end_day = 0


class G2PSeasonalActualLine(models.Model):
    _name = "g2p.seasonal.actual.line"
    _description = "Seasonal Crop Actual Line"


    crop_registry_id = fields.Many2one("g2p.crop.registry", string="Crop Registry", ondelete="cascade")
    sync_id = fields.Char(string="Sync ID", default=lambda self: str(uuid.uuid4()))
    land_info_id = fields.Many2one('g2p.land.information', string="Land ID")
    region_name_id = fields.Many2one('g2p.region', string='Region')
    zone_name_id = fields.Many2one('g2p.zone', string='Zone')
    woreda_name_id = fields.Many2one('g2p.woreda', string='Woreda')
    kebele_id = fields.Many2one('g2p.kebele', string='Kebele')
    gps = fields.Char(string='GPS Coordinates')

    ownership_type = fields.Selection([('owner', 'Owner'), ('tenant', 'Tenant'), ('crop_share', 'Crop Sharing'), ('family_gift', 'Family Gift')], string="Ownership Type")
    land_area = fields.Float(string="Total Land Area (ha)")
    land_category = fields.Selection([('seasonal', 'Seasonal Crop'), ('horticulture', 'Horticulture Crop')], string="Plot Category")
    soil_fertility = fields.Char(string="Soil Fertility")
    season_id = fields.Many2one('g2p.season', string="Season", required=True)

    @api.onchange('land_info_id')
    def _onchange_land_info_id(self):
        if self.land_info_id:
            self.land_area = self.land_info_id.total_land_area
            self.ownership_type = self.land_info_id.ownership_type
            if hasattr(self.land_info_id, 'soil_fertility') and self.land_info_id.soil_fertility:
                self.soil_fertility = self.land_info_id.soil_fertility.lower()
            if self.land_info_id.land_kebele:
                self.kebele_id = self.land_info_id.land_kebele.id
                if self.land_info_id.land_kebele.woreda:
                    self.woreda_name_id = self.land_info_id.land_kebele.woreda.id
                    if self.land_info_id.land_kebele.woreda.zone:
                        self.zone_name_id = self.land_info_id.land_kebele.woreda.zone.id
                        if self.land_info_id.land_kebele.woreda.zone.region:
                            self.region_name_id = self.land_info_id.land_kebele.woreda.zone.region.id
                        else:
                            self.region_name_id = False
                    else:
                        self.zone_name_id = False
                        self.region_name_id = False
                else:
                    self.woreda_name_id = False
                    self.zone_name_id = False
                    self.region_name_id = False
            else:
                self.kebele_id = False
                self.woreda_name_id = False
                self.zone_name_id = False
                self.region_name_id = False

            if hasattr(self.land_info_id, 'polygon_data') and self.land_info_id.polygon_data:
                self.gps = self.land_info_id.polygon_data
            else:
                self.gps = False
                
            if self.crop_registry_id:
                planned_line = self.crop_registry_id.seasonal_line_ids.filtered(
                    lambda l: l.land_info_id.id == self.land_info_id.id
                )
                if planned_line:
                    planned_line = planned_line[0]
                    water_resources = []
                    for w in planned_line.water_resource_line_ids:
                        water_resources.append((0, 0, {
                            'water_resource_id': w.water_resource_id.id,
                            'method_id': w.method_id,
                            'frequency': w.frequency,
                            'crop_registry_id': self.crop_registry_id.id,
                        }))
                    if water_resources:
                        self.water_resource_line_ids = [(5, 0, 0)] + water_resources
    crop_name_id = fields.Many2one("g2p.crop", string="Crop", required=True)
    collected_gc = fields.Date(string="Actual Planted Date (GC)")
    collected_ec = fields.Char(string="Actual Planted Date (EC)")
    crop_category_id = fields.Many2one("g2p.crop.category", string="Crop Category", compute="_compute_crop_category", store=True, readonly=True)
    crop_variety_id = fields.Many2one("g2p.crop.variety", string="Crop Variety")
    remark = fields.Char(string="Remark")
    actual_crop_area = fields.Float(string="Actual Crop Area (ha)")
    actual_growth_duration = fields.Float(string="Actual Growth Duration (days)")
    
    actual_seed_class = fields.Selection([('local', 'Local'), ('improved', 'Improved')], string="Seed Type")
    actual_seed_qty = fields.Float(string="Actual Seed Quantity (kg)")
    actual_fertilizer_type = fields.Selection([
        ('organic', 'Organic'),
        ('inorganic', 'Inorganic'),
        ('biofertilizer', 'Bio Fertilizer')
    ], string="Actual Fertilizer Type")
    actual_fertilizer_name = fields.Many2one('g2p.fertilizer', string="Actual Fertilizer Name", domain="[('category', '=', actual_fertilizer_type)]")
    actual_fertilizer_qty = fields.Float(string="Actual Fertilizer Quantity (kg)")
    actual_fertilizer_sack = fields.Float(string="Actual Fertilizer Sacks Count", compute="_compute_actual_fertilizer_sacks", store=True)

    has_cluster_farming = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string="Have you done any cluster farming or related activities earlier?")
    actual_cluster_plan = fields.Float(string="Actual Cluster Plan")
    actual_cluster_collected_land = fields.Float(string="Actual Cluster Collected Land")
    actual_cluster_collected_quintal = fields.Float(string="Actual Cluster Collected Quintal")
    actual_cluster_participant_farmers = fields.Integer(string="Actual Cluster Participant Farmers")
    actual_collected_land = fields.Float(string="Actual Collected Land")
    actual_collected_land_quintal = fields.Float(string="Actual Collected Land Quintal")
    actual_collected_by_combiner = fields.Float(string="Actual Collected by Combiner")
    
    pest_occurrence = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Pest Occurrence")
    pest_line_ids = fields.One2many('g2p.crop.pest.line', 'actual_seasonal_line_id', string="Pest Details")
    
    weed_occurrence = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Weed Occurrence")
    weed_line_ids = fields.One2many('g2p.crop.weed.line', 'actual_seasonal_line_id', string="Weed Details")
    
    actual_yield = fields.Float(string="Actual Yield (ha)")
    cultivated_by = fields.Selection([
        ('tractor', 'Tractor'),
        ('other', 'Other'),
    ], string="Cultivation Type")
    land_prep_method_ids = fields.Many2many("g2p.land.prep.method", string="Land Prep Methods")
    
    water_resource_line_ids = fields.One2many(
        "g2p.actual.water.resource.line",
        "actual_seasonal_line_id",
        string="Water Resources",
    )
    
    start_gc = fields.Date(string="Start GC")
    start_month = fields.Integer(string="Start Month", compute="_compute_start_date", store=True)
    start_day = fields.Integer(string="Start Day", compute="_compute_start_date", store=True)
    end_gc = fields.Date(string="End GC")
    end_month = fields.Integer(string="End Month", compute="_compute_end_date", store=True)
    end_day = fields.Integer(string="End Day", compute="_compute_end_date", store=True)
    
    is_mismatch = fields.Boolean(string="Mismatch", compute="_compute_is_mismatch", store=True)

    @api.onchange('actual_crop_area')
    def _onchange_actual_crop_area(self):
        if self.crop_registry_id and self.actual_crop_area and self.land_info_id:
            same_land_lines = self.crop_registry_id.actual_seasonal_line_ids.filtered(lambda l: l.land_info_id == self.land_info_id)
            total_actual = sum(same_land_lines.mapped('actual_crop_area'))
            max_area = self.land_info_id.total_land_area
            if total_actual > max_area:
                attempted_area = self.actual_crop_area
                allocated_area = total_actual - attempted_area
                remaining_area = max_area - allocated_area
                
                if remaining_area < 0:
                    remaining_area = 0.0
                    
                self.actual_crop_area = 0.0
                return {
                    'warning': {
                        'title': "Area Exceeded",
                        'message': "You entered %.2f ha, but only %.2f ha is remaining out of the total %.2f ha (%.2f ha is already allocated to other actual crops)." % (attempted_area, remaining_area, max_area, allocated_area)
                    }
                }

    @api.depends('actual_fertilizer_qty')
    def _compute_actual_fertilizer_sacks(self):
        for rec in self:
            if rec.actual_fertilizer_qty:
                rec.actual_fertilizer_sack = rec.actual_fertilizer_qty / 50.0
            else:
                rec.actual_fertilizer_sack = 0.0

    @api.onchange('actual_fertilizer_qty')
    def _onchange_fertilizer_qty(self):
        for rec in self:
            if rec.actual_fertilizer_qty:
                rec.actual_fertilizer_sack = rec.actual_fertilizer_qty / 50.0
            else:
                rec.actual_fertilizer_sack = 0.0

    @api.onchange('season_id')
    def _onchange_season_id(self):
        if self.season_id:
            self.start_gc = self.season_id.start_gc
            self.end_gc = self.season_id.end_gc
            if self.season_id.start_gc:
                self.start_month = self.season_id.start_gc.month
                self.start_day = self.season_id.start_gc.day
            if self.season_id.end_gc:
                self.end_month = self.season_id.end_gc.month
                self.end_day = self.season_id.end_gc.day
            # Clear the actual planted date so user enters fresh date for new season
            self.collected_gc = False
            self.collected_ec = False

    @api.depends("start_gc")
    def _compute_start_date(self):
        for record in self:
            if record.start_gc:
                record.start_month = record.start_gc.month
                record.start_day = record.start_gc.day
            else:
                record.start_month = record.start_day = 0

    @api.depends("end_gc")
    def _compute_end_date(self):
        for record in self:
            if record.end_gc:
                record.end_month = record.end_gc.month
                record.end_day = record.end_gc.day
            else:
                record.end_month = record.end_day = 0

    @api.depends("crop_name_id")
    def _compute_crop_category(self):
        for rec in self:
            if rec.crop_name_id:
                rec.crop_category_id = rec.crop_name_id.category.id
            else:
                rec.crop_category_id = False

    @api.depends("crop_name_id", "crop_variety_id", "collected_gc", "season_id",
                 "crop_registry_id.seasonal_line_ids",
                 "crop_registry_id.seasonal_line_ids.crop_name_id",
                 "crop_registry_id.seasonal_line_ids.crop_variety_id",
                 "crop_registry_id.seasonal_line_ids.collected_gc",
                 "crop_registry_id.seasonal_line_ids.season_id")
    def _compute_is_mismatch(self):
        for rec in self:
            if not rec.crop_registry_id or not rec.crop_name_id:
                rec.is_mismatch = False
                continue
            planned_lines = rec.crop_registry_id.seasonal_line_ids
            matched = False
            for planned in planned_lines:
                if (planned.crop_name_id.id == rec.crop_name_id.id
                        and planned.crop_variety_id.id == rec.crop_variety_id.id
                        and planned.season_id.id == rec.season_id.id
                        and planned.collected_gc == rec.collected_gc):
                    matched = True
                    break
            rec.is_mismatch = not matched

    @api.depends("crop_name_id")
    def _compute_crop_category(self):
        for rec in self:
            rec.crop_category_id = (
                rec.crop_name_id.category.id
                if rec.crop_name_id
                else False
            )

    @api.onchange("crop_name_id")
    def _onchange_crop(self):
        self.crop_variety_id = False
        return {
            "domain": {
                "crop_variety_id": [
                    ("crop_id", "=", self.crop_name_id.id)
                ]
            }
        }

    @api.onchange("collected_gc")
    def _onchange_collected_gc(self):
        if self.collected_gc:
            if self.collected_gc > fields.Date.today():
                self.collected_gc = False
                return {
                    'warning': {
                        'title': 'Invalid Date',
                        'message': 'Actual Planted Date (GC) cannot be a future date.'
                    }
                }
            cdate = date(
                self.collected_gc.year,
                self.collected_gc.month,
                self.collected_gc.day,
            )
            ethiopian_date = eth_date.to_ethiopian(
                cdate.year, cdate.month, cdate.day
            )
            self.collected_ec = eth_date.convert_tuple_to_string_with_separator(
                ethiopian_date
            )

    @api.onchange("collected_ec")
    def _onchange_collected_ec(self):
        if self.collected_ec:
            eth_date.check_ethipian_date_str(self.collected_ec, future_date=True)
            date_list = re.split("[-/,]", self.collected_ec)
            gc_date = eth_date.to_gregorian(
                int(date_list[2]), int(date_list[1]), int(date_list[0])
            )
            self.collected_gc = gc_date

class G2PPest(models.Model):
    _name = "g2p.pest"
    _description = "Pest Name"
    name = fields.Char("Name", required=True)
    code = fields.Char("Code")
    pest_type = fields.Selection([
        ('insect_pests', 'Insect Pests'),
        ('rodent_pests', 'Rodent Pests'),
        ('molluscan_pests', 'Molluscan Pests'),
        ('disease_pests', 'Disease-causing Pests'),
    ], string="Pest Type")

class G2PPesticide(models.Model):
    _name = "g2p.pesticide"
    _description = "Pesticide Name"
    name = fields.Char("Name", required=True)
    code = fields.Char("Code")
    pesticide_type = fields.Selection([
        ('insecticide', 'Insecticide'),
        ('fungicide', 'Fungicide'),
        ('herbicide', 'Herbicide'),
        ('rodenticide', 'Rodenticide'),
        ('bactericide', 'Bactericide'),
        ('nematicide', 'Nematicide'),
        ('acaricide', 'Acaricide / Miticide'),
        ('molluscicide', 'Molluscicide'),
        ('termiticide', 'Termiticide'),
        ('avicide', 'Avicide'),
        ('piscicide', 'Piscicide'),
        ('algicide', 'Algicide'),
        ('virucide', 'Virucide'),
    ], string="Type")

class G2PCropPestLine(models.Model):
    _name = "g2p.crop.pest.line"
    _description = "Crop Pest Details"

    crop_registry_id = fields.Many2one('g2p.crop.registry', string="Crop Registry", ondelete="cascade")
    actual_seasonal_line_id = fields.Many2one("g2p.seasonal.actual.line", ondelete="cascade")
    seasonal_line_id = fields.Many2one('g2p.seasonal.line', ondelete="cascade")
    actual_horticulture_line_id = fields.Many2one("g2p.horticulture.actual.line", ondelete="cascade")
    horticulture_line_id = fields.Many2one('g2p.horticulture.line', ondelete="cascade")
    
    pest_type = fields.Selection([
        ('insect_pests', 'Insect Pests'),
        ('rodent_pests', 'Rodent Pests'),
        ('molluscan_pests', 'Molluscan Pests'),
        ('disease_pests', 'Disease-causing Pests'),
    ], string="Pest Type")
    pest_name_id = fields.Many2one('g2p.pest', string="Pest Name", domain="[('pest_type', '=', pest_type)]")
    
    pesticides_type = fields.Selection([
        ('insecticide', 'Insecticide'),
        ('fungicide', 'Fungicide'),
        ('herbicide', 'Herbicide'),
        ('rodenticide', 'Rodenticide'),
        ('bactericide', 'Bactericide'),
        ('nematicide', 'Nematicide'),
        ('acaricide', 'Acaricide / Miticide'),
        ('molluscicide', 'Molluscicide'),
        ('termiticide', 'Termiticide'),
        ('avicide', 'Avicide'),
        ('piscicide', 'Piscicide'),
        ('algicide', 'Algicide'),
        ('virucide', 'Virucide'),
    ], string="Pesticides Type")
    pesticide_name_id = fields.Many2one('g2p.pesticide', string="Pesticide Name", domain="[('pesticide_type', '=', pesticides_type)]")
    pesticide_method = fields.Char(string="Method of Control")
    pesticide_frequency = fields.Char(string="Frequency of Application")

class G2PWeed(models.Model):
    _name = "g2p.weed"
    _description = "Weed Name"
    name = fields.Char("Name", required=True)
    code = fields.Char("Code")
    weed_type = fields.Selection([
        ('by_life_cycle', 'By Life Cycle'),
        ('by_season', 'By Season'),
        ('by_botanical_nature', 'By Botanical Nature'),
        ('by_habitat', 'By Habitat'),
        ('by_harmfulness', 'By Harmfulness'),
        ('by_morphology', 'By Morphology'),
    ], string="Weed Type")

class G2PCropWeedLine(models.Model):
    _name = "g2p.crop.weed.line"
    _description = "Crop Weed Details"

    crop_registry_id = fields.Many2one('g2p.crop.registry', string="Crop Registry", ondelete="cascade")
    actual_seasonal_line_id = fields.Many2one("g2p.seasonal.actual.line", ondelete="cascade")
    seasonal_line_id = fields.Many2one('g2p.seasonal.line', ondelete="cascade")
    actual_horticulture_line_id = fields.Many2one("g2p.horticulture.actual.line", ondelete="cascade")
    horticulture_line_id = fields.Many2one('g2p.horticulture.line', ondelete="cascade")
    
    weed_type = fields.Selection([
        ('by_life_cycle', 'By Life Cycle'),
        ('by_season', 'By Season'),
        ('by_botanical_nature', 'By Botanical Nature'),
        ('by_habitat', 'By Habitat'),
        ('by_harmfulness', 'By Harmfulness'),
        ('by_morphology', 'By Morphology'),
    ], string="Weed Type")
    weed_name_id = fields.Many2one('g2p.weed', string="Weed Name", domain="[('weed_type', '=', weed_type)]")
    
    weedicide_type = fields.Selection([
        ('pre_emergent', 'Pre-emergent Herbicide'),
        ('post_emergent', 'Post-emergent Herbicide'),
        ('systemic', 'Systemic Herbicide'),
        ('contact', 'Contact Herbicide'),
        ('graminicide', 'Graminicide'),
        ('broadleaf', 'Broadleaf Herbicide'),
        ('sedge', 'Sedge Herbicide'),
        ('aquatic', 'Aquatic Herbicide'),
        ('foliar', 'Foliar Herbicide'),
        ('soil', 'Soil Herbicide'),
    ], string="Weedicides Type")
    weedicide_name_id = fields.Many2one('g2p.weedicide', string="Weedicides Name", domain="[('weedicide_type', '=', weedicide_type)]")
    pesticide_method = fields.Char(string="Method of Control")
    pesticide_frequency = fields.Char(string="Frequency of Application")

class G2PWeedicide(models.Model):
    _name = "g2p.weedicide"
    _description = "Weedicide Name"
    name = fields.Char("Name", required=True)
    code = fields.Char("Code")
    weedicide_type = fields.Selection([
        ('pre_emergent', 'Pre-emergent Herbicide'),
        ('post_emergent', 'Post-emergent Herbicide'),
        ('systemic', 'Systemic Herbicide'),
        ('contact', 'Contact Herbicide'),
        ('graminicide', 'Graminicide'),
        ('broadleaf', 'Broadleaf Herbicide'),
        ('sedge', 'Sedge Herbicide'),
        ('aquatic', 'Aquatic Herbicide'),
        ('foliar', 'Foliar Herbicide'),
        ('soil', 'Soil Herbicide'),
    ], string="Type")



