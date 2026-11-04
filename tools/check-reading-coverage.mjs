// Optional local client helper. No network, storage or progress upload.
import {createHash} from 'node:crypto';
const hash=s=>createHash('sha256').update(s).digest('hex');
const normalizeSpeech=s=>s.normalize('NFKC').replace(/[\p{P}\p{Z}\s]/gu,'');
export function checkReadingCoverage(manifest,receipts,{skipped_parts=[]}={}){
 const expected=manifest.expected_parts,byId=new Map(expected.map(p=>[p.part_id,p])),seen=new Set(),duplicates=[],stale=[],unknown=[],fetched=[],written=[],spoken=[],order=[];let interrupted=false;
 for(const r of receipts){
  if(r.chapter_cache_key!==manifest.chapter_cache_key){stale.push(r.part_id);continue;}
  const part=byId.get(r.part_id);if(!part){unknown.push(r.part_id);continue;}if(seen.has(r.part_id))duplicates.push(r.part_id);seen.add(r.part_id);order.push(part.order);
  const source=typeof r.fetched_text==='string'&&hash(r.fetched_text)===part.sha256;if(source)fetched.push(r.part_id);
  if(source&&typeof r.written_text==='string'&&r.written_text===r.fetched_text)written.push(r.part_id);
  if(r.interrupted)interrupted=true;
  if(source&&!r.interrupted&&r.spoken_evidence==='actual_transcript'&&typeof r.spoken_transcript==='string'&&normalizeSpeech(r.spoken_transcript)===normalizeSpeech(r.fetched_text))spoken.push(r.part_id);
 }
 const hasAll=ids=>expected.every(p=>ids.includes(p.part_id)),ordered=order.length===expected.length&&order.every((n,i)=>n===expected[i].order),clean=!duplicates.length&&!stale.length&&!unknown.length&&!skipped_parts.length;
 const writtenComplete=hasAll(written)&&ordered&&clean,spokenComplete=hasAll(spoken)&&ordered&&clean&&!interrupted;
 return {fetched_complete:hasAll(fetched),written_complete:writtenComplete,spoken_status:spokenComplete?'spoken_verified':'spoken_unverified',missing_fetched:expected.filter(p=>!fetched.includes(p.part_id)).map(p=>p.part_id),missing_written:expected.filter(p=>!written.includes(p.part_id)).map(p=>p.part_id),missing_spoken:expected.filter(p=>!spoken.includes(p.part_id)).map(p=>p.part_id),duplicates,stale,unknown,out_of_order:!ordered,interrupted,intentional_skips:skipped_parts,scope:'Checks supplied client text evidence only. It cannot authenticate audio/transcript provenance, control playback or infer understanding.',no_remote_progress:true};
}
