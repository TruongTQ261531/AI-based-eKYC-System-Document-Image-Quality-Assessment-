"""Server-owned active liveness state machine; never accepts client measurements."""
import hashlib
import secrets
from collections import deque

import numpy as np

from .io import StageError


PROMPTS = {
    'calibrate': 'Nhìn thẳng vào camera, mở hai mắt và giữ đầu ổn định để căn chỉnh.',
    'blink': 'Chớp cả hai mắt chậm một lần: nhắm khoảng nửa giây rồi mở ra.',
    'turn_left': 'Quay đầu nhẹ sang TRÁI của bạn, giữ một chút rồi nhìn thẳng lại.',
    'turn_right': 'Quay đầu nhẹ sang PHẢI của bạn, giữ một chút rồi nhìn thẳng lại.',
    'look_left': 'Giữ đầu thẳng, chỉ đưa mắt nhìn sang TRÁI của bạn rồi nhìn camera lại.',
    'look_right': 'Giữ đầu thẳng, chỉ đưa mắt nhìn sang PHẢI của bạn rồi nhìn camera lại.',
    'nod': 'Cúi đầu nhẹ xuống, giữ một chút rồi trở lại nhìn thẳng.',
    'return_center': 'Trở lại nhìn thẳng vào camera và mở hai mắt.',
    'passed': 'Đã hoàn thành thử thách. Nhìn thẳng và chụp ảnh chân dung trong 45 giây.',
}

HINTS = {
    'face_missing':'Chưa thấy khuôn mặt. Đưa toàn bộ mặt vào khung.',
    'multiple_faces':'Có nhiều khuôn mặt. Chỉ một người được xuất hiện trong khung.',
    'face_too_small':'Đưa camera gần hơn để nhìn rõ khuôn mặt và hai mắt.',
    'face_too_close':'Lùi camera một chút để toàn bộ mặt nằm trong khung.',
    'face_outside':'Giữ cả trán, cằm và hai bên mặt trong ảnh.',
    'face_off_center':'Đưa khuôn mặt về giữa khung.',
    'face_dark':'Tăng ánh sáng phía trước khuôn mặt, tránh ngược sáng.',
    'face_bright':'Giảm ánh sáng chiếu thẳng vào mặt để giữ chi tiết.',
    'face_blur':'Giữ máy ổn định, lau ống kính và chờ lấy nét.',
    'face_tilted':'Giữ đầu thẳng, tránh nghiêng sang vai.',
    'face_extreme_pose':'Quay hoặc cúi nhẹ hơn để camera vẫn nhìn rõ mặt.',
    'gaze_unavailable':'Chưa theo dõi rõ mắt. Nhìn camera, tránh phản chiếu mạnh trên kính.',
    'identity_changed':'Khuôn mặt giữa các lượt chưa nhất quán. Hãy bắt đầu lại với cùng một người.',
    'face_lost':'Khuôn mặt bị mất khỏi khung quá lâu. Hãy bắt đầu lại thử thách.',
    'repeated_frame':'Các khung hình bị lặp. Kiểm tra camera đang truyền hình trực tiếp.',
    'challenge_timeout':'Hết thời gian thực hiện. Hãy bắt đầu lại và làm theo từng hướng dẫn.',
    'identity_samples_missing':'Chưa thu được đủ mẫu khuôn mặt rõ. Giữ mặt thẳng và thử lại.',
    'spoof_detected':'Từ chối: phát hiện dấu hiệu khuôn mặt qua màn hình hoặc ảnh giả. Bỏ điện thoại/ảnh đang đưa trước camera và thực hiện lại bằng khuôn mặt trực tiếp.',
    'pad_uncertain':'Chưa đủ bằng chứng khuôn mặt trực tiếp. Đưa màn hình/ảnh ra khỏi khung, tăng ánh sáng đều và giữ rõ toàn bộ mặt.',
    'pad_unavailable':'Bộ kiểm tra chống giả chưa sẵn sàng. Không thể tiếp tục xác thực; vui lòng thử lại sau.',
}


class ChallengeRequestError(ValueError):
    pass


class LiveChallenge:
    lifetime = 180.
    proof_lifetime = 45.
    face_grace_seconds = 6.

    def __init__(self, now, match_threshold=.363):
        self.id = secrets.token_urlsafe(24)
        self.frame_token = secrets.token_urlsafe(24)
        self.sequence = 0
        self.created = now
        self.last_received = None
        self.last_good = now
        self.last_sample = -float('inf')
        self.match_threshold = match_threshold
        self.actions = ['blink','turn_left','turn_right','nod']
        secrets.SystemRandom().shuffle(self.actions)
        self.index = 0
        self.status = 'running'
        self.reason = None
        self.phase = 'calibrate'
        self.baseline_samples = []
        self.baseline = None
        self.neutral_count = self.hold_count = 0
        self.hold_started = None
        self.blink_closed = None
        self.armed = False
        self.embeddings = []
        self.hashes = deque(maxlen=128)
        self.repeats = 0
        self.passed_at = None
        self.checked_frames = 0
        self.good_frames = 0
        self.pad_checked_frames = 0
        self.pad_live_frames = 0
        self.pad_consecutive_live = 0
        self.pad_decision = 'pending'

    def validate(self, challenge_id, frame_token, sequence, now):
        if self.id != challenge_id or not secrets.compare_digest(self.frame_token, frame_token or '') or sequence != self.sequence:
            raise ChallengeRequestError('Khung hình không đúng phiên hoặc sai thứ tự. Hãy bắt đầu lại thử thách.')
        if self.status != 'running':
            raise ChallengeRequestError('Thử thách đã kết thúc. Hãy bắt đầu lại nếu cần.')
        if self.last_received is not None and now-self.last_received < .07:
            raise ChallengeRequestError('Khung hình gửi quá nhanh. Vui lòng thử lại.')

    def fail(self, reason):
        self.status, self.reason = 'failed', reason
        self.embeddings.clear()

    @staticmethod
    def eyes_open(observation):
        return max(observation['blink_left'],observation['blink_right']) < .28

    def deltas(self, observation):
        pose = observation['pose']
        gaze = observation.get('gaze_horizontal')
        return (pose['yaw']-self.baseline['yaw'], pose['pitch']-self.baseline['pitch'],
                None if gaze is None or self.baseline['gaze'] is None else gaze-self.baseline['gaze'])

    def neutral(self, observation):
        yaw,pitch,_ = self.deltas(observation)
        return abs(yaw)<10 and abs(pitch)<10 and self.eyes_open(observation)

    def report(self, now, observation=None, hint=None):
        action = 'passed' if self.status=='passed' else ('calibrate' if self.baseline is None else self.actions[min(self.index,len(self.actions)-1)])
        prompt = PROMPTS.get(action,'')
        if self.phase == 'return_center' and self.status=='running': prompt = PROMPTS['return_center']
        if self.status == 'failed': prompt = HINTS.get(self.reason,'Hãy bắt đầu lại thử thách.')
        measurements=None
        if self.baseline is not None and observation and observation.get('pose'):
            yaw,pitch,gaze=self.deltas(observation)
            measurements=dict(yaw_delta=float(yaw),pitch_delta=float(pitch),
                              gaze_delta=None if gaze is None else float(gaze),
                              gaze_direction='unknown' if gaze is None else
                              'left' if gaze>.055 else 'right' if gaze<-.055 else 'center')
        return dict(status=self.status, challenge_id=self.id, frame_token=self.frame_token,
                    next_sequence=self.sequence, action=action, phase=self.phase,
                    instruction=hint or prompt, completed=self.index, total=len(self.actions),
                    expires_in=max(0.,round(self.created+self.lifetime-now,1)),
                    proof_expires_in=max(0.,round(self.passed_at+self.proof_lifetime-now,1)) if self.passed_at else 0,
                    reason=self.reason, observation=observation,measurements=measurements,
                    liveness_checked=self.status=='passed', liveness_passed=self.status=='passed',
                    method='server_random_motion_challenge_v1', presentation_attack_detection='not_certified',
                    pad=dict(method='minifasnet_v2_v1se_rgb_v1', decision=self.pad_decision,
                             checked_frames=self.pad_checked_frames))

    def proof_valid(self, now):
        return (self.status=='passed' and self.pad_consecutive_live>=6 and self.passed_at is not None
                and 0 <= now-self.passed_at <= self.proof_lifetime)

    def summary(self):
        return dict(checked=self.status=='passed',passed=self.status=='passed',
                    method='server_random_motion_challenge_v1',
                    completed_actions=self.actions[:self.index], checked_frames=self.checked_frames,
                    good_frames=self.good_frames, identity_samples=len(self.embeddings),
                    identity_consistent=self.status=='passed',
                    presentation_attack_detection='not_certified',
                    pad=dict(method='minifasnet_v2_v1se_rgb_v1', checked_frames=self.pad_checked_frames,
                             live_frames=self.pad_live_frames, passed=self.status=='passed' and self.pad_consecutive_live>=6),
                    limitation='RGB PAD model + active motion; local replay/relay, camera injection and deepfake accuracy are not validated.')

    def update(self, observation, image, now, extract):
        self.last_received = now
        self.sequence += 1
        self.frame_token = secrets.token_urlsafe(24)
        self.checked_frames += 1
        # One visible deadline governs the whole challenge. A hidden per-step or
        # frame-count timeout used to stop the trial while the UI still had time.
        # Existing nonce/rate checks and bounded buffers still bound resource use.
        if now-self.created >= self.lifetime:
            self.fail('challenge_timeout')
            return self.report(now)
        digest = hashlib.sha256(image.tobytes()).digest()
        if digest in self.hashes:
            self.repeats += 1
            if self.repeats >= 3: self.fail('repeated_frame')
            return self.report(now, observation, HINTS['repeated_frame'])
        self.hashes.append(digest)
        if observation.get('face_count',0)>1:
            self.fail('multiple_faces')
            return self.report(now,observation)
        if observation.get('face_count') != 1:
            self.pad_consecutive_live = 0
            self.pad_decision = 'pending'
        if observation.get('face_count') == 1:
            pad = observation.get('pad') or {}
            decision = pad.get('decision')
            if decision not in ('live','spoof','uncertain'):
                self.fail('pad_unavailable')
                return self.report(now,observation)
            self.pad_decision = decision
            self.pad_checked_frames += 1
            self.pad_consecutive_live = self.pad_consecutive_live+1 if decision=='live' else 0
            if decision=='spoof':
                self.fail('spoof_detected')
                return self.report(now,observation)
            if decision=='live': self.pad_live_frames += 1
        if not observation.get('quality_ok'):
            self.neutral_count = self.hold_count = 0
            self.hold_started = self.blink_closed = None
            self.armed = False
            if now-self.last_good > self.face_grace_seconds and self.baseline is not None:
                self.fail('face_lost')
                return self.report(now,observation)
            problems = observation.get('problems') or ['face_missing']
            return self.report(now,observation,HINTS.get(problems[0],HINTS['face_missing']))
        self.last_good = now
        if self.pad_decision != 'live':
            self.neutral_count = self.hold_count = 0
            self.hold_started = self.blink_closed = None
            self.armed = False
            self.baseline_samples.clear()
            return self.report(now,observation,HINTS['pad_uncertain'])
        self.good_frames += 1
        pose = observation['pose']
        # Identity samples are taken in modest poses throughout the challenge.
        if now-self.last_sample >= .7 and abs(pose['yaw']) < 28 and abs(pose['pitch']) < 28:
            self.last_sample = now
            try:
                _, embedding, _ = extract(image)
                vector = np.asarray(embedding,dtype=np.float32).reshape(1,-1)
                norm = np.linalg.norm(vector)
                if not np.isfinite(vector).all() or norm < 1e-8: raise StageError('Invalid sample')
                vector /= norm
                if self.embeddings and min(float((e @ vector.T).item()) for e in self.embeddings) < self.match_threshold:
                    self.fail('identity_changed')
                    return self.report(now,observation)
                if len(self.embeddings) < 12: self.embeddings.append(vector.copy())
            except StageError:
                pass
        if self.baseline is None:
            gaze = observation.get('gaze_horizontal')
            if (abs(pose['yaw'])>15 or abs(pose['pitch'])>22 or abs(pose['roll'])>15 or
                    not self.eyes_open(observation)):
                self.baseline_samples.clear()
                return self.report(now,observation,PROMPTS['calibrate'])
            # Gaze remains informative, but is not required by the four core actions.
            self.baseline_samples.append([pose['yaw'],pose['pitch'],np.nan if gaze is None else gaze])
            if len(self.baseline_samples)>=4 and len(self.embeddings)>=2:
                values=np.array(self.baseline_samples[-4:])
                if np.ptp(values[:,0])<5 and np.ptp(values[:,1])<5:
                    gaze_values=values[np.isfinite(values[:,2]),2]
                    self.baseline=dict(yaw=float(np.median(values[:,0])),pitch=float(np.median(values[:,1])),
                                       gaze=float(np.median(gaze_values)) if len(gaze_values) else None)
                    self.phase='action'
                self.baseline_samples=self.baseline_samples[-4:]
            return self.report(now,observation)
        neutral = self.neutral(observation)
        self.neutral_count = self.neutral_count+1 if neutral else 0
        if self.phase=='return_center':
            if self.neutral_count>=2:
                if self.index == len(self.actions)-1 and self.pad_consecutive_live<6:
                    return self.report(now,observation,'Giữ mặt thẳng thêm một chút để hoàn tất kiểm tra chống giả.')
                self.index+=1
                if self.index == len(self.actions):
                    if len(self.embeddings)<3:
                        self.index-=1; self.fail('identity_samples_missing')
                    else:
                        self.status='passed'; self.phase='complete'; self.passed_at=now
                else:
                    self.phase='action'; self.armed=True
                    self.hold_count=0; self.hold_started=self.blink_closed=None
            return self.report(now,observation)
        if not self.armed:
            if self.neutral_count>=2: self.armed=True
            return self.report(now,observation,PROMPTS['return_center'] if not self.armed else None)
        action=self.actions[self.index]
        yaw,pitch,gaze=self.deltas(observation)
        triggered=False
        if action=='blink':
            if min(observation['blink_left'],observation['blink_right'])>.55 and abs(yaw)<10 and abs(pitch)<10:
                if self.blink_closed is None: self.blink_closed=now
            elif self.eyes_open(observation) and self.blink_closed is not None:
                triggered=.08<=now-self.blink_closed<=1.8
                self.blink_closed=None
            elif self.blink_closed is not None and now-self.blink_closed>1.8:
                self.blink_closed=None
        else:
            active = ((action=='turn_left' and 14<=yaw<=40 and abs(pitch)<15) or
                      (action=='turn_right' and -40<=yaw<=-14 and abs(pitch)<15) or
                      (action=='nod' and 10<=pitch<=30 and abs(yaw)<10) or
                      (action=='look_left' and gaze is not None and gaze>=.065 and abs(yaw)<7 and abs(pitch)<8) or
                      (action=='look_right' and gaze is not None and gaze<=-.065 and abs(yaw)<7 and abs(pitch)<8))
            active = active and self.eyes_open(observation)
            if active:
                if self.hold_started is None: self.hold_started=now
                self.hold_count+=1
                triggered=self.hold_count>=2 and now-self.hold_started>=.25
            else:
                self.hold_started=None; self.hold_count=0
        if triggered:
            self.phase='return_center'; self.neutral_count=0
        return self.report(now,observation)
