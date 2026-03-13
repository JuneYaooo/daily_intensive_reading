from marshmallow import Schema, fields, validate

class SourceSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    url = fields.Str()
    description = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class PromptSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    content = fields.Str(required=True)
    description = fields.Str()
    type = fields.Str(validate=validate.OneOf(["filter", "summary", "general"]), default="general")
    is_default = fields.Bool(default=False)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class TagSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    created_at = fields.DateTime(dump_only=True)

class FavoriteCardSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1))
    source_url = fields.Str()
    conclusion = fields.Str()
    key_points = fields.List(fields.Str())
    quotes = fields.List(fields.Str())
    author = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

class ReportGenerationSchema(Schema):
    content = fields.Str(required=True)
    source_id = fields.Int(required=False)
    prompt_id = fields.Int(required=False)
    prompt_content = fields.Str(required=False)
    prompt_type = fields.Str(validate=validate.OneOf(["filter", "summary", "general"]), required=False)

class CardGenerationSchema(Schema):
    selected_content = fields.Str(required=True)
    prompt_id = fields.Int()
    title = fields.Str()
    author = fields.Str()
    source = fields.Str()
    tags = fields.List(fields.Str()) 