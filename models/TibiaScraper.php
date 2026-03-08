<?php

declare(strict_types=1);

namespace Models;

class TibiaScraper
{
    public function fetchGuildMembers(string $guildUrl): array
    {
        $html = $this->fetchHtml($guildUrl);
        if (!$html) {
            return [];
        }

        $dom = new \DOMDocument();
        @$dom->loadHTML($html);
        $xpath = new \DOMXPath($dom);
        $rows = $xpath->query('//table//tr');
        $members = [];

        foreach ($rows as $row) {
            $cells = $row->getElementsByTagName('td');
            if ($cells->length < 3) {
                continue;
            }
            $name = trim($cells->item(0)?->textContent ?? '');
            $vocation = trim($cells->item(1)?->textContent ?? '');
            $level = (int) preg_replace('/\D+/', '', $cells->item(2)?->textContent ?? '0');
            $statusText = strtolower($row->textContent);
            if ($name === '' || $level <= 0) {
                continue;
            }

            $members[] = [
                'name' => $name,
                'vocation' => $vocation,
                'level' => $level,
                'online_status' => str_contains($statusText, 'online') ? 'online' : 'offline',
            ];
        }

        return $members;
    }

    public function fetchCharacter(string $url): ?array
    {
        $html = $this->fetchHtml($url);
        if (!$html) {
            return null;
        }

        preg_match('/Name:\s*<\/td><td[^>]*>([^<]+)/i', $html, $nameMatch);
        preg_match('/Vocation:\s*<\/td><td[^>]*>([^<]+)/i', $html, $vocMatch);
        preg_match('/Level:\s*<\/td><td[^>]*>(\d+)/i', $html, $levelMatch);
        preg_match('/Guild membership:\s*<\/td><td[^>]*>([^<]+)/i', $html, $guildMatch);

        $name = trim($nameMatch[1] ?? '');
        if ($name === '') {
            return null;
        }

        return [
            'name' => $name,
            'vocation' => trim($vocMatch[1] ?? ''),
            'level' => (int) ($levelMatch[1] ?? 0),
            'guild' => trim($guildMatch[1] ?? ''),
            'status' => str_contains(strtolower($html), 'currently online') ? 'online' : 'offline',
        ];
    }

    private function fetchHtml(string $url): ?string
    {
        $context = stream_context_create([
            'http' => ['timeout' => 15, 'header' => "User-Agent: NeverDualityPanel/1.0\r\n"],
            'ssl' => ['verify_peer' => false, 'verify_peer_name' => false],
        ]);

        $html = @file_get_contents($url, false, $context);

        return $html !== false ? $html : null;
    }
}
