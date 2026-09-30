"""
arriendos/schema.py
Personaliza Swagger:
 - Agrupa los endpoints por secciones con el atributo 'swagger_tag' de cada vista.
 - Muestra una frase descriptiva junto a cada ruta con el diccionario 'swagger_resumenes'
   de cada vista (clave = acción del ViewSet o método HTTP en minúscula).
"""
from drf_spectacular.openapi import AutoSchema


class EsquemaConTags(AutoSchema):
    def get_tags(self):
        return [getattr(self.view, 'swagger_tag', 'General')]

    def get_summary(self):
        resumenes = getattr(self.view, 'swagger_resumenes', {})
        clave = getattr(self.view, 'action', None) or self.method.lower()
        return resumenes.get(clave) or super().get_summary()
