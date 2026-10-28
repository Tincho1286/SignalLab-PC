"""Use the same readable integer-sequence notation as inverse Z."""
from .result_summary import transform_summary

def inverse_dtft_summary(request,result):
    values={k:v for k,v in result.items() if k!='infinity_included'}
    summary=transform_summary({'operation':'z_inverse_expression','expression':request['expression']},values)
    summary.title='DTFT inversa algebraica'
    for section in summary.sections:
        if section.title=='Cómo interpretarlo':section.paragraphs=[result['scope']]
        section.rows=[('ROC de X(z) asociado' if key=='Región de convergencia' else key,value) for key,value in section.rows]
    return summary
