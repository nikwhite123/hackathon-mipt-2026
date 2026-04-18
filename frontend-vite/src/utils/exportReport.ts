/**
 * Renders DOM nodes to canvas and builds a multi-page PDF report (dashboard export).
 */
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

export const generatePDFReport = async (elementIds: string[]) => {
    const pdf = new jsPDF('p', 'mm', 'a4');

    let isFirstPage = true;

    for (const id of elementIds) {
        const original = document.getElementById(id);
        if (original) {
            if (!isFirstPage) {
                pdf.addPage();
            }

            const pageContainer = document.createElement('div');
            pageContainer.style.width = '800px';
            pageContainer.style.background = '#ffffff';
            pageContainer.style.padding = '40px';
            pageContainer.style.fontFamily = "'Segoe UI', Arial, sans-serif";

            pageContainer.innerHTML = `
                <div style="border-bottom: 4px solid #7733FF; padding-bottom: 20px; margin-bottom: 30px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h1 style="color: #101828; margin: 0; font-size: 28px;">RT Infra Security</h1>
                            <p style="color: #FF4F12; margin: 5px 0 0 0; font-weight: bold; font-size: 14px; text-transform: uppercase;">Отчет по информационной безопасности</p>
                        </div>
                        <div style="text-align: right; color: #667085; font-size: 11px;">
                            <p style="margin: 0;">Дата: ${new Date().toLocaleDateString('ru-RU')}</p>
                        </div>
                    </div>
                </div>
            `;

            const sectionTitle = original.getAttribute('data-report-name');
            if (sectionTitle) {
                const h3 = document.createElement('h3');
                h3.innerText = sectionTitle;
                h3.style.color = '#101828';
                h3.style.fontSize = '22px';
                h3.style.marginBottom = '20px';
                h3.style.borderLeft = '6px solid #7733FF';
                h3.style.paddingLeft = '15px';
                pageContainer.appendChild(h3);
            }

            const elementCanvas = await html2canvas(original, {
                scale: 2,
                useCORS: true,
                backgroundColor: '#ffffff'
            });

            const img = document.createElement('img');
            img.src = elementCanvas.toDataURL('image/png');
            img.style.width = '100%';
            img.style.borderRadius = '8px';
            img.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
            pageContainer.appendChild(img);

            const footer = document.createElement('div');
            footer.innerHTML = `
                <div style="margin-top: 40px; border-top: 1px solid #eee; padding-top: 15px; text-align: center; color: #98A2B3; font-size: 10px;">
                    Страница ${isFirstPage ? '1' : pdf.getNumberOfPages()} | Сгенерировано системой RT Infra Security
                </div>
            `;
            pageContainer.appendChild(footer);

            document.body.appendChild(pageContainer);
            const finalPageCanvas = await html2canvas(pageContainer, { scale: 2 });
            document.body.removeChild(pageContainer);

            const imgData = finalPageCanvas.toDataURL('image/png');

            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();

            const canvasWidth = finalPageCanvas.width;
            const canvasHeight = finalPageCanvas.height;
            const ratio = canvasWidth / canvasHeight;

            let printWidth = pdfWidth;
            let printHeight = pdfWidth / ratio;

            const maxPrintHeight = pdfHeight - 20;
            if (printHeight > maxPrintHeight) {
                printHeight = maxPrintHeight;
                printWidth = printHeight * ratio;
            }

            const xOffset = (pdfWidth - printWidth) / 2;
            const yOffset = 5;

            pdf.addImage(imgData, 'PNG', xOffset, yOffset, printWidth, printHeight);

            isFirstPage = false;
        }
    }

    pdf.save(`RT-Security-Report-${Date.now()}.pdf`);
};