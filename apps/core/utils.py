import csv
from django.http import HttpResponse
from django.utils import timezone

def export_to_csv(queryset, fields, filename_prefix="export"):
    """
    Generic utility to export a queryset to CSV.
    """
    response = HttpResponse(content_type='text/csv')
    filename = f"{filename_prefix}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write Header
    writer.writerow([field.split('__')[-1].replace('_', ' ').title() for field in fields])
    
    # Write Data
    for obj in queryset:
        row = []
        for field in fields:
            value = obj
            for part in field.split('__'):
                value = getattr(value, part, '')
            
            if callable(value):
                try:
                    value = value()
                except:
                    value = ''
            
            row.append(value)
        writer.writerow(row)
        
    return response
