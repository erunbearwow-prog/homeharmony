from .models import LogoColors


def logo_colors(request):
    """
    Контекстный процессор для передачи цветов и изображений логотипа.
    """
    try:
        colors = LogoColors.get_active()
        return {
            'logo_colors': {
                # Заливки
                'circle_fill': colors.get_fill('circle', request),
                'circle_fill_type': colors.get_fill_type('circle'),
                'circle_opacity': colors.circle_opacity,

                'curved_top_fill': colors.get_fill('curved_top', request),
                'curved_top_fill_type': colors.get_fill_type('curved_top'),
                'curved_top_opacity': colors.curved_top_opacity,

                'bottom_triangle_fill': colors.get_fill('bottom_triangle', request),
                'bottom_triangle_fill_type': colors.get_fill_type('bottom_triangle'),
                'bottom_triangle_opacity': colors.bottom_triangle_opacity,

                'left_top_fill': colors.get_fill('left_top', request),
                'left_top_fill_type': colors.get_fill_type('left_top'),
                'left_top_opacity': colors.left_top_opacity,

                'right_top_fill': colors.get_fill('right_top', request),
                'right_top_fill_type': colors.get_fill_type('right_top'),
                'right_top_opacity': colors.right_top_opacity,

                'curved_left_fill': colors.get_fill('curved_left', request),
                'curved_left_fill_type': colors.get_fill_type('curved_left'),
                'curved_left_opacity': colors.curved_left_opacity,

                'curved_right_fill': colors.get_fill('curved_right', request),
                'curved_right_fill_type': colors.get_fill_type('curved_right'),
                'curved_right_opacity': colors.curved_right_opacity,

                # Обводка
                'stroke_color': colors.stroke_color,
                'stroke_width': colors.stroke_width,
                'stroke_opacity': colors.stroke_opacity,
                'stroke_dasharray': colors.stroke_dasharray,
                'stroke_linecap': colors.stroke_linecap,
                'stroke_linejoin': colors.stroke_linejoin,

                'circle_stroke': colors.circle_stroke,
                'circle_stroke_width': colors.circle_stroke_width,
                'circle_stroke_dasharray': colors.circle_stroke_dasharray,
            }
        }
    except:
        # Дефолтные значения
        return {
            'logo_colors': {
                'circle_fill': '#7B3F8A',
                'circle_fill_type': 'color',
                'circle_opacity': 0.85,

                'curved_top_fill': '#E8E5E0',
                'curved_top_fill_type': 'color',
                'curved_top_opacity': 1.0,

                'bottom_triangle_fill': '#E8E5E0',
                'bottom_triangle_fill_type': 'color',
                'bottom_triangle_opacity': 1.0,

                'left_top_fill': '#C4B5A6',
                'left_top_fill_type': 'color',
                'left_top_opacity': 1.0,

                'right_top_fill': '#B0B8C0',
                'right_top_fill_type': 'color',
                'right_top_opacity': 1.0,

                'curved_left_fill': '#A89888',
                'curved_left_fill_type': 'color',
                'curved_left_opacity': 1.0,

                'curved_right_fill': '#889098',
                'curved_right_fill_type': 'color',
                'curved_right_opacity': 1.0,

                'stroke_color': '#B0A898',
                'stroke_width': 0.8,
                'stroke_opacity': 0.3,
                'stroke_dasharray': '',
                'stroke_linecap': 'round',
                'stroke_linejoin': 'round',

                'circle_stroke': '#7B3F8A',
                'circle_stroke_width': 1.0,
                'circle_stroke_dasharray': '',
            }
        }