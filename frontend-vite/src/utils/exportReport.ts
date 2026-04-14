import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export const generatePDFReport = async (elementIds: string[]) => {
    const reportContainer = document.createElement('div');
    reportContainer.id = "temp-report-container";
    reportContainer.style.position = 'absolute';
    reportContainer.style.left = '-9999px';
    reportContainer.style.top = '0';
    reportContainer.style.width = '800px';
    reportContainer.style.background = '#ffffff';
    reportContainer.style.padding = '40px';
    reportContainer.style.zIndex = '-1';

    reportContainer.innerHTML = `
        <div style="border-bottom: 3px solid #7733FF; padding-bottom: 20px; margin-bottom: 30px; font-family: Arial, sans-serif;">
            <h1 style="color: #101828; margin: 0; font-size: 28px;">RT Infra Security: Отчет</h1>
            <p style="color: #FF4F12; margin: 0; font-weight: bold; font-size: 16px;">Система мониторинга и анализа угроз</p>
            <p style="color: #667085; margin-top: 10px; font-size: 12px;">Дата формирования: ${new Date().toLocaleString('ru-RU')}</p>
        </div>
    `;

    for (const id of elementIds) {
        const original = document.getElementById(id);
        if (original) {

            const sectionTitle = original.getAttribute('data-report-name');
            if (sectionTitle) {
                const h3 = document.createElement('h3');
                h3.innerText = sectionTitle;
                h3.style.fontFamily = 'Arial, sans-serif';
                h3.style.color = '#475467';
                reportContainer.appendChild(h3);
            }

            const elementCanvas = await html2canvas(original, { scale: 2, useCORS: true });
            const img = document.createElement('img');
            img.src = elementCanvas.toDataURL('image/png');
            img.style.width = '100%';
            img.style.marginBottom = '30px';

            reportContainer.appendChild(img);
        }
    }

    document.body.appendChild(reportContainer);

    try {
        const finalCanvas = await html2canvas(reportContainer, {
            scale: 2,
            useCORS: true,
            backgroundColor: '#ffffff'
        });

        const imgData = finalCanvas.toDataURL('image/png');
        const pdf = new jsPDF('p', 'mm', 'a4');
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (finalCanvas.height * pdfWidth) / finalCanvas.width;

        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
        pdf.save(`RT-Security-Report-${Date.now()}.pdf`);
    } catch (err) {
        console.error("Ошибка экспорта:", err);
    } finally {
        document.body.removeChild(reportContainer);
    }
};