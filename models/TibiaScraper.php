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

        return $this->parseGuildMembersHtml($html);
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

    private function parseGuildMembersHtml(string $html): array
    {
        $dom = new \DOMDocument();
        @$dom->loadHTML($html);
        $xpath = new \DOMXPath($dom);

        $memberRows = $xpath->query('//table//tr');
        $members = [];

        foreach ($memberRows as $row) {
            $cells = $row->getElementsByTagName('td');
            if ($cells->length < 5) {
                continue;
            }

            $name = trim($cells->item(1)?->textContent ?? '');
            $vocation = trim($cells->item(2)?->textContent ?? '');
            $levelRaw = trim($cells->item(3)?->textContent ?? '');
            $level = (int) preg_replace('/\D+/', '', $levelRaw);
            $statusRaw = trim($cells->item(4)?->textContent ?? '');
            $statusLower = strtolower($statusRaw);

            if (!preg_match('/^\d+$/', preg_replace('/\s+/', '', $levelRaw))) {
                continue;
            }

            if (!str_contains($statusLower, 'online') && !str_contains($statusLower, 'offline')) {
                continue;
            }

            $status = str_contains($statusLower, 'online') ? 'online' : 'offline';

            if ($name === '' || $level <= 0) {
                continue;
            }

            $members[] = [
                'name' => $name,
                'vocation' => $vocation,
                'level' => $level,
                'online_status' => $status,
            ];
        }

        return $members;
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
