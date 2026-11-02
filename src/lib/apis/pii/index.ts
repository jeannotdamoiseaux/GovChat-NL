// GovChat-NL: persoonsgegevensfilter
import { WEBUI_API_BASE_URL } from '$lib/constants';

export type PiiFinding = {
	index: number;
	category: string;
	label: string | null;
	text: string;
	maskable: boolean;
	detail: string | null;
};

export type PiiSegment = {
	text: string;
	finding?: number;
};

export type PiiDetection = {
	enabled: boolean;
	findings: PiiFinding[];
	segments: PiiSegment[];
};

export type PiiMode = 'off' | 'warn' | 'mask';

const request = async (token: string, method: string, path: string, body?: object) => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/pii${path}`, {
		method,
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`
		},
		...(body ? { body: JSON.stringify(body) } : {})
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			console.error(err);
			error = err.detail ?? err;
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};

export const detectPii = async (token: string, text: string): Promise<PiiDetection> =>
	request(token, 'POST', '/detect', { text });

export const maskPii = async (
	token: string,
	text: string,
	exclude: number[] = []
): Promise<{ text: string; replacements: { category: string; label: string }[] }> =>
	request(token, 'POST', '/mask', { text, exclude });

export type PiiFileFinding = PiiFinding & {
	before: string;
	after: string;
};

export type PiiFileDetection = {
	enabled: boolean;
	findings: PiiFileFinding[];
	// Totaal aantal treffers; bij grote bestanden staan ze niet allemaal in findings
	total: number;
	masked?: boolean;
};

export const detectPiiInFile = async (token: string, id: string): Promise<PiiFileDetection> =>
	request(token, 'POST', `/files/${id}/detect`, {});

export const maskPiiInFile = async (
	token: string,
	id: string,
	exclude: number[] = []
): Promise<{ replacements: number; content: string }> =>
	request(token, 'POST', `/files/${id}/mask`, { exclude });

/**
 * Zet een tekstcontrole om naar de vorm van een bestandscontrole, met een
 * stukje tekst voor en na elke treffer (voor tijdelijke chats, waar het
 * bestand niet op de server staat).
 */
export const toFileDetection = (detection: PiiDetection, contextChars = 40): PiiFileDetection => {
	const findings: PiiFileFinding[] = detection.findings.map((f) => ({
		...f,
		before: '',
		after: ''
	}));
	detection.segments.forEach((segment, i) => {
		if (segment.finding === undefined || !findings[segment.finding]) return;
		const prev = detection.segments[i - 1];
		const next = detection.segments[i + 1];
		findings[segment.finding].before = (prev?.text ?? '').slice(-contextChars).trimStart();
		findings[segment.finding].after = (next?.text ?? '').slice(0, contextChars).trimEnd();
	});
	return { enabled: detection.enabled, findings, total: findings.length };
};

export const getPiiConfig = async (token: string) => request(token, 'GET', '/config');

export const setPiiConfig = async (token: string, config: object) =>
	request(token, 'POST', '/config', config);

/**
 * Bepaal de modus voor deze chat.
 * - De beheerder zet het filter aan of uit.
 * - "Altijd filteren" van de agent of de beheerder is bindend.
 * - Verder wint de keuze in de chat, dan die van de agent, dan de standaard.
 */
export const resolvePiiMode = (
	enabled: boolean,
	defaultMode: PiiMode | undefined,
	agentMode: PiiMode | undefined | null,
	chatMode: PiiMode | undefined | null
): { mode: PiiMode; locked: boolean } => {
	if (!enabled) {
		return { mode: 'off', locked: true };
	}
	const base: PiiMode = agentMode ?? defaultMode ?? 'warn';
	if (base === 'mask') {
		return { mode: 'mask', locked: true };
	}
	return { mode: chatMode ?? base, locked: false };
};

export const PII_CATEGORY_LABELS: Record<string, string> = {
	bsn: 'BSN',
	iban: 'IBAN',
	geboortedatum: 'Geboortedatum',
	naam: 'Naam',
	email: 'E-mailadres',
	telefoon: 'Telefoonnummer',
	adres: 'Adres',
	postcode: 'Postcode',
	id_document: 'Paspoort- of ID-nummer',
	rijbewijs: 'Rijbewijsnummer',
	v_nummer: 'V-nummer',
	kenteken: 'Kenteken',
	creditcard: 'Creditcardnummer',
	ip_adres: 'IP-adres',
	bijzonder: 'Bijzondere persoonsgegevens'
};

export const PII_SPECIAL_LABELS: Record<string, string> = {
	gezondheid: 'gezondheid',
	religie: 'religie of levensovertuiging',
	afkomst: 'etnische afkomst',
	politiek: 'politieke voorkeur',
	vakbond: 'vakbondslidmaatschap',
	seksuele_geaardheid: 'seksuele geaardheid',
	strafrechtelijk: 'strafrechtelijke gegevens'
};
