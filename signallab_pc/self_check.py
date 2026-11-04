"""Comprobación ejecutable del paquete; no equivale a la auditoría de paridad."""
import json
import os
import sys
import traceback
from pathlib import Path


def run(destination):
    report = {"frozen": bool(getattr(sys, "frozen", False)),
              "migration_complete": False, "checks": {}}
    try:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        import numpy as np
        import scipy
        import sympy
        import matplotlib
        from PySide6.QtWidgets import QApplication
        from .workbench import WorkbenchWindow as ToolboxWindow
        from .workspaces import ROUTES
        from .state_space import StateModel
        from .model import Signal
        from .operations import dft, idft
        from .filters import Transfer, bilinear
        x = Signal([1, 2, 3, 4])
        np.testing.assert_allclose(idft(dft(x)).values, x.values)
        report["checks"]["fft_roundtrip"] = True
        np.testing.assert_allclose(Transfer([1], [1, -.5]).excitation_response(4).values, [1, .5, .25, .125])
        report["checks"]["lti_recurrence"] = True
        np.testing.assert_allclose(bilinear(Transfer([1], [1, 1], "analog"), 1).a, [1, -1/3])
        report["checks"]["bilinear"] = True
        t = sympy.Symbol("t")
        assert sympy.integrate(t, (t, 0, 1)) == sympy.Rational(1, 2)
        report["checks"]["symbolic_runtime"] = True
        app = QApplication.instance() or QApplication([])
        window = ToolboxWindow()
        assert window.category == 'Inicio'
        item=ROUTES['state_space','simulation']
        window.open_tool(item)
        assert window.current_operation==item
        panel=window.pages[tuple(item)].panel
        model=panel.read_model()
        time,output,states=model.simulate(np.ones(11),step=.1)
        np.testing.assert_allclose(output[:,0],1-np.exp(-time),atol=1e-13)
        np.testing.assert_allclose(output[:,1],(1-np.exp(-2*time))/2,atol=1e-13)
        key=window.publish(model,operation='Diagnóstico portable')
        restored=window.project.get(key)
        np.testing.assert_allclose(restored.A,model.A)
        panel.figure.clear();axis=panel.figure.add_subplot(111);axis.plot(time,output.real);panel.canvas.draw();app.processEvents()
        delay=StateModel.from_transfer(Transfer([0,1],[1]),.1)
        np.testing.assert_allclose(delay.simulate([1,2,3])[1][:,0],[0,1,2])
        np.testing.assert_allclose(delay.to_transfer().response([.2,1]),np.exp(-1j*np.array([.2,1])),atol=1e-13)
        report['checks']['state_space_simulation_and_project'] = True
        report['checks']['digital_delay_transfer_roundtrip'] = True
        report['checks']['toolbox_menu_and_matplotlib'] = True
        from .sampling import sample_expression
        from .project_picker import ProjectPicker
        from .report_view import ReportView
        sampling_item=ROUTES['sampling',0]
        window.open_tool(sampling_item);window.resize(1366,768);window.show()
        page=window.pages[tuple(sampling_item)];page.panel._accept_signal(sample_expression('cos(2*pi*t)',0,100,101))
        from .plot_view import open_result_plot
        open_result_plot(page.output,window)
        app.processEvents()
        assert page.output.canvas.isVisible() and page.output.canvas.figure.axes
        assert window.stack.currentWidget().active_page is page
        picker=ProjectPicker(window,'signal',domains=['discrete']);picker.search.setText('Muestrear')
        assert len(picker.visible)==1 and picker.selected_id
        picker.accept_selection();assert picker.result()==1
        original='Resultado\n\n'+json.dumps({'operation':'sampling','samples':101})
        formatted=ReportView();formatted.setPlainText(original);assert formatted.toPlainText()==original
        report['checks']['sampling_plot_and_report_layout'] = True
        report['checks']['project_picker_search_and_selection'] = True
        report['checks']['formatted_report_preserves_text'] = True
        from .symbolic_process import run_request
        measure=run_request({'operation':'signal_measures_expression','expression':'exp(-abs(t))','domain':'continuous','mode':'global'})
        assert measure['energy']['exact']=='1' and measure['mean_square']['exact']=='0'
        sampled=run_request({'operation':'signal_measures_window','expression':'1+i*n','domain':'discrete','start':'-1','stop':'2'})
        assert sampled['energy']==10 and len(sampled['samples'])==4
        measure_item=ROUTES['expression_measures','global']
        window.open_tool(measure_item);app.processEvents()
        assert window.pages[tuple(measure_item)].panel.expression.text()=='exp(-abs(t))'
        report['checks']['packaged_symbolic_measures_and_window'] = True
        report['checks']['expression_measure_menu'] = True
        window.hide();window.deleteLater()
        report["versions"] = {"numpy": np.__version__, "scipy": scipy.__version__,
                              "sympy": sympy.__version__, "matplotlib": matplotlib.__version__}
        report["ok"] = True
    except Exception:
        report["ok"] = False
        report["error"] = traceback.format_exc()
    Path(destination).write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0 if report["ok"] else 1
