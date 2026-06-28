from odoo import fields, models


class G2PFertilizer(models.Model):
    _name = "g2p.fertilizer"
    _description = "Fertilizer"
    _order = "category, name"

    name = fields.Char(string="Fertilizer Name", required=True)
    code = fields.Char(string="Code")
    category = fields.Selection([
        ('organic', 'Organic Fertilizers (Natural & Soil-Friendly)'),
        ('nitrogen', 'Nitrogen Fertilizers (For Leaf Growth)'),
        ('phosphorus', 'Phosphorus Fertilizers (For Root & Flower Growth)'),
        ('potassium', 'Potassium Fertilizers (For Strength & Disease Resistance)'),
        ('npk', 'Complex / Mixed Fertilizers (NPK)'),
        ('micronutrient', 'Micronutrient Fertilizers (Small but Essential)'),
    ], string="Fertilizer Category", required=True)
