# notification.py
import requests
import re

class Notification:
    def send_lotto_buying_message(self, body: dict, webhook_url: str) -> None:
        """
        로또 구매 후 Discord/Webhook 알림
        """
        assert isinstance(webhook_url, str)

        result = body.get("result", {})
        return_msg = result.get("resultMsg", "")
        # 실패 시 에러 메시지 전송
        if return_msg.upper() != "SUCCESS":
            error_code = result.get("resultCode", "UNKNOWN")
            message = (
                f"🚨 로또 구매 오류 발생\n"
                f"코드: {error_code}\n"
                f"메시지: {return_msg}"
            )
            self._send_discord_webhook(webhook_url, message)
            return

        # 성공 시 번호 전송
        lotto_number_str = self.make_lotto_number_message(result["arrGameChoiceNum"])
        buy_round = result.get("buyRound", "")
        balance = body.get("balance", "")
        message = (
            f"✅ {buy_round}회차 로또 구매 완료 :moneybag:\n"
            f"남은 잔액: {balance}원\n"
            f"```{lotto_number_str}```"
        )
        self._send_discord_webhook(webhook_url, message)

    def make_lotto_number_message(self, lotto_number: list) -> str:
        """
        로또 번호 리스트를 메시지 문자열로 변환
        """
        assert isinstance(lotto_number, list)

        # parse list without last number 3
        lotto_number = [x[:-1] for x in lotto_number]
        # remove '|' and convert to spaced string
        lotto_number = [x.replace("|", " ") for x in lotto_number]
        return "\n".join(lotto_number)

    def send_win720_buying_message(self, body: dict, webhook_url: str) -> None:
        """
        연금복권 구매 후 Discord/Webhook 알림
        """
        assert isinstance(webhook_url, str)

        result_code = body.get("resultCode", "")
        result_msg  = body.get("resultMsg", "")
        # 실패 시 에러 메시지 전송
        if result_code != "100":
            message = (
                f"🚨 연금복권 구매 오류 발생\n"
                f"코드: {result_code}\n"
                f"메시지: {result_msg}"
            )
            self._send_discord_webhook(webhook_url, message)
            return

        # 성공 시 번호 전송
        # saleTicket 포맷: "<...>|<...>|<...>|회차|번호,번호,..."
        sale_ticket = body.get("saleTicket", "")
        parts = sale_ticket.split("|")
        win720_round = parts[3] if len(parts) > 3 else ""
        tickets = parts[4].split(",") if len(parts) > 4 else []
        win720_number_str = self.make_win720_number_message(tickets)
        balance = body.get("balance", "")
        message = (
            f"✅ {win720_round}회차 연금복권 구매 완료 :moneybag:\n"
            f"남은 잔액: {balance}원\n"
            f"```{win720_number_str}```"
        )
        self._send_discord_webhook(webhook_url, message)

    def make_win720_number_message(self, win720_numbers: list) -> str:
        """
        연금복권 티켓 정보를 메시지 문자열로 변환
        """
        lines = []
        for idx, ticket in enumerate(win720_numbers, start=1):
            # ticket 예: "1조1234"
            formatted = f"[{idx}] {ticket[0]}조 {' '.join(ticket[1:])}"
            lines.append(formatted)
        return "\n".join(lines)

    def send_lotto_winning_message(self, winning: dict, webhook_url: str) -> None:
        """
        로또 당첨 내역을 Discord/Webhook 알림
        """
        assert isinstance(winning, dict)
        assert isinstance(webhook_url, str)

        try:
            # 상세 결과 포맷
            max_len = max(len(f"{ln['label']} {ln['status']}") for ln in winning["lotto_details"])
            formatted_lines = []
            for ln in winning["lotto_details"]:
                label_status = f"{ln['label']} {ln['status']}".ljust(max_len)
                nums = []
                for num in ln["result"]:
                    raw = re.search(r'\d+', num).group()
                    fmt = f"{int(raw):02d}"
                    nums.append(f"[{fmt}]" if '✨' in num else f" {fmt} ")
                nums = [f"{n:>6}" for n in nums]
                formatted_lines.append(f"{label_status} " + " ".join(nums))

            results_block = "\n".join(formatted_lines)
            money = winning.get("money", "-")
            if money != "-":
                win_msg = f"로또 *{winning['round']}회* - *{money}* 당첨 되었습니다 🎉"
            else:
                win_msg = f"로또 *{winning['round']}회* - 다음 기회에... 🫠"

            self._send_discord_webhook(
                webhook_url,
                f"```ini\n{results_block}```\n{win_msg}"
            )
        except KeyError:
            # 데이터 없으면 무시
            return

    def send_win720_winning_message(self, winning: dict, webhook_url: str) -> None:
        """
        연금복권 당첨 내역을 Discord/Webhook 알림
        """
        assert isinstance(winning, dict)
        assert isinstance(webhook_url, str)

        try:
            money = winning.get("money", "-")
            if money != "-":
                msg = f"연금복권 *{winning['round']}회* - *{money}* 당첨 되었습니다 🎉"
            else:
                msg = f"연금복권 *{winning['round']}회* - 다음 기회에... 🫠"
            self._send_discord_webhook(webhook_url, msg)
        except KeyError:
            self._send_discord_webhook(webhook_url, "연금복권 당첨 정보 조회 실패")

    def _send_discord_webhook(self, webhook_url: str, message: str) -> None:
        """
        Discord Webhook으로 메시지 전송
        """
        payload = {"content": message}
        requests.post(webhook_url, json=payload)
