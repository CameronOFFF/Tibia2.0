<?php

declare(strict_types=1);

namespace Models;

class ReportExporter
{
    public function exportWeekly(array $rows, string $path): string
    {
        $filename = 'guild_week_report_' . date('Y_m_d') . '.xlsx';
        $fullPath = rtrim($path, '/') . '/' . $filename;

        if (class_exists('PhpOffice\\PhpSpreadsheet\\Spreadsheet')) {
            $spreadsheet = new \PhpOffice\PhpSpreadsheet\Spreadsheet();
            $sheet = $spreadsheet->getActiveSheet();
            $sheet->fromArray(['Nome', 'Vocação', 'Level Atual', 'Level Up na Semana'], null, 'A1');

            $line = 2;
            foreach ($rows as $row) {
                $sheet->fromArray([$row['character_name'], $row['vocation'], $row['level_current'], $row['level_gain']], null, 'A' . $line++);
            }

            $writer = new \PhpOffice\PhpSpreadsheet\Writer\Xlsx($spreadsheet);
            $writer->save($fullPath);

            return $filename;
        }

        $fp = fopen($fullPath, 'w');
        fputcsv($fp, ['Nome', 'Vocação', 'Level Atual', 'Level Up na Semana']);
        foreach ($rows as $row) {
            fputcsv($fp, [$row['character_name'], $row['vocation'], $row['level_current'], $row['level_gain']]);
        }
        fclose($fp);

        return $filename;
    }
}
