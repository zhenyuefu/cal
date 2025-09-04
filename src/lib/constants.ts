export const PARCOURS = ["ANDROIDE","DAC","STL","IMA","BIM","SAR","SESI","SFPN"] as const;
export const MASTER_YEARS = ["M1","M2"] as const;
export const BASE = "https://cal.ufr-info-p6.jussieu.fr/caldav.php/{parcours}/{master_year}_{parcours}/";
export const TZID_DEFAULT = "Europe/Paris";

export type MasterYear = typeof MASTER_YEARS[number];
export type Parcours = typeof PARCOURS[number];

