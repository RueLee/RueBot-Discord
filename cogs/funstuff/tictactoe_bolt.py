import asyncio
import io
import random

import discord
from discord import app_commands
from discord.ext import commands
from matplotlib import pyplot as plt

from ..components.tictactoe_bolt.board import Board, InvalidMoveError
from ..components.tictactoe_bolt.ai import Board_AI, save_q_table

ACTIVE_PLAYER_SESSION = {}

def add_player_session(interaction: discord.Interaction, message: discord.Message, player_name: discord.Member) -> None:
    ACTIVE_PLAYER_SESSION[interaction.user] = message
    ACTIVE_PLAYER_SESSION[player_name if player_name is not None else f"AI_{message.id}"] = message.id

def delete_player_session(message: discord.Message) -> None:
    message_id_removal = [key for key, val in ACTIVE_PLAYER_SESSION.items() if val == message]
    for key in message_id_removal:
        del ACTIVE_PLAYER_SESSION[key]

class PlaceButton(discord.ui.View):
    def __init__(self, board: Board, board_ai: Board_AI, to_play_human: bool, message: discord.Message):
        super().__init__(timeout=300)
        self.board = board
        self.board_ai = board_ai
        self.to_play_human = to_play_human
        self.message = message

    @discord.ui.button(label="Place", style=discord.ButtonStyle.green)
    async def place(self, interaction: discord.Interaction, button: discord.Button):
        if interaction.message.id not in ACTIVE_PLAYER_SESSION.values():
            await interaction.response.send_message(f"We can't find a username in this message record!", ephemeral=True)
            return

        curr_turn = self.board.get_current_turns()
        if interaction.user.name != self.board.player_sym_def[curr_turn]:
            await interaction.response.send_message(f"Wait for your turn!", ephemeral=True)
            return

        await interaction.response.send_modal(PlaceModal(self.board, self.board_ai, self.to_play_human, title="TTT_Modal"))

    async def on_timeout(self) -> None:
        await self.message.edit(content="Session timed out after 5 min!", view=None)

        delete_player_session(self.message)

class PlaceModal(discord.ui.Modal):
    grid_placement = discord.ui.TextInput(label="Enter row and column numbers", placeholder="Format: <row> <column>",
                                               required=True, style=discord.TextStyle.short)

    def __init__(self, board: Board, board_ai: Board_AI, to_play_human: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ttt_board = board
        self.ttt_board_ai = board_ai
        self.to_play_human = to_play_human

    async def check_winner(self, interaction: discord.Interaction) -> (bool, float):
        reward = 0
        winner_string = self.ttt_board.check_winning_position()
        if winner_string != "":
            embed = discord.Embed(title=f"{" | ".join(value for value in self.ttt_board.player_sym_def.values())}\nCurrent Turn: {self.ttt_board.get_current_turns()}", description=self.ttt_board.get_board_string())
            embed.set_footer(text=f"{self.ttt_board.player_sym_def[winner_string]} has won as {self.ttt_board.get_current_turns()}")
            await interaction.message.edit(embed=embed, view=None)
            # await interaction.response.send_message(f"{self.ttt_board.player_sym_def[winner_string]} has won as {self.ttt_board.get_current_turns()}")
            delete_player_session(interaction.message)
            score_penalty = self.ttt_board.turn_counter - self.ttt_board.max_turns
            score_reward = self.ttt_board.max_turns - self.ttt_board.turn_counter
            reward = score_penalty if self.ttt_board.player_sym_def[winner_string] != "AI" else score_reward
            return True, reward
        elif self.ttt_board.turn_counter >= self.ttt_board.max_turns:
            embed = discord.Embed(title=f"{" | ".join(value for value in self.ttt_board.player_sym_def.values())}\nCurrent Turn: {self.ttt_board.get_current_turns()}", description=self.ttt_board.get_board_string())
            embed.set_footer(text="Game ended in a draw on a max turn threshold!")
            await interaction.message.edit(embed=embed, view=None)
            # await interaction.response.send_message(f"Game ended in a draw on a max turn threshold!")
            delete_player_session(interaction.message)
            reward = 0.5
            return True, reward
        return False, reward

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()
        row_col = self.grid_placement.value.strip().split()
        if len(row_col) != 2:
            await interaction.followup.send("ERROR: More than two arguments entered!", ephemeral=True)
            return

        try:
            state = str(self.ttt_board.board)
            move = (int(row_col[0]) - 1, int(row_col[1]) - 1)
            self.ttt_board.make_move(move)
            next_state = str(self.ttt_board.board)
            is_there_winner, reward = await self.check_winner(interaction)
            next_action = self.ttt_board.get_all_possible_moves()
            self.ttt_board_ai.update_q_value(state, move, reward, next_state, next_action)
            if is_there_winner:
                # save_q_table(self.ttt_board_ai.q_table)
                return
            self.ttt_board.cycle_turns()

            embed = discord.Embed(title=f"{" | ".join(value for value in self.ttt_board.player_sym_def.values())}\nCurrent Turn: {self.ttt_board.get_current_turns()}", description=self.ttt_board.get_board_string())
            await interaction.message.edit(embed=embed)
            # await interaction.response.send_message(".", delete_after=0.001)
            if self.to_play_human:
                return

            # AI's Move
            state = str(self.ttt_board.board)
            ai_move = self.ttt_board_ai.choose_action(state)
            self.ttt_board.make_move(ai_move)
            next_state = str(self.ttt_board.board)
            is_there_winner, reward = await self.check_winner(interaction)
            next_action = self.ttt_board.get_all_possible_moves()
            self.ttt_board_ai.update_q_value(state, move, reward, next_state, next_action)
            if is_there_winner:
                # save_q_table(self.ttt_board_ai.q_table)
                return
            self.ttt_board.cycle_turns()
            embed = discord.Embed(title=f"{" | ".join(value for value in self.ttt_board.player_sym_def.values())}\nCurrent Turn: {self.ttt_board.get_current_turns()}", description=self.ttt_board.get_board_string())
            await interaction.message.edit(embed=embed)
        except InvalidMoveError:
            if self.ttt_board.player_sym_def[self.ttt_board.get_current_turns()] == "AI":
                await interaction.message.edit(content="Player has won after AI made an invalid move!", view=None)
                delete_player_session(interaction.message)
            else:
                await interaction.followup.send("Invalid move made! Please try another input!", ephemeral=True)

class TicTaeToeBolt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(description="Tic Tac Toe Bolt, a game from GiiKER. NOTE: A timeout will occur after 5 mins of session!")
    @app_commands.describe(player_name="Select a player to play against OR leave empty to play against AI.")
    @app_commands.choices(symbol=[
        app_commands.Choice(name="O", value="O"),
        app_commands.Choice(name="X", value="X")
    ])
    async def tttb_play(self, interaction: discord.Interaction, symbol: str, player_name: discord.Member=None):
        await interaction.response.defer()
        message = await interaction.original_response()

        if interaction.user in ACTIVE_PLAYER_SESSION:
            await interaction.followup.send(f"You have an active game session!\n{ACTIVE_PLAYER_SESSION[interaction.user].jump_url}")
            return

        if player_name is not None:
            if player_name not in interaction.guild.members:
                await interaction.response.send_message(f"Can't find a player name in this server!", ephemeral=True)
                return
            await player_name.send(f"{interaction.user} requests to play Tic-Tac-Toe-Bolt!\n{message.jump_url}")

        # if symbol.upper() not in ["O", "X"]:
        #     await interaction.response.send_message(f"Invalid symbol!", ephemeral=True)
        #     return

        opponent_name = "AI" if player_name is None else player_name.name
        player_o = interaction.user.name if symbol.upper() == "O" else opponent_name
        player_x = opponent_name if symbol.upper() == "O" else interaction.user.name
        ttt_board = await asyncio.to_thread(lambda : Board(player_o, player_x))
        ttt_board_ai = None
        if player_name is None:
            ttt_board_ai = await asyncio.to_thread(lambda : Board_AI(ttt_board, "X" if symbol.upper() == "O" else "O"))
        try:
            ttt_string = ttt_board.get_board_string()
            embed = discord.Embed(title=f"{player_o} | {player_x}\nCurrent Turn: {ttt_board.get_current_turns()}", description=ttt_string)

            await message.edit(embed=embed, view=PlaceButton(ttt_board, ttt_board_ai, True if player_name is not None else False, message))

            add_player_session(interaction, message, player_name)

            if ttt_board.get_current_turns() != symbol and player_name is None:
                state = str(ttt_board.board)
                ai_move = ttt_board_ai.choose_action(state)
                ttt_board.make_move(ai_move)
                next_state = str(ttt_board.board)
                next_action = ttt_board.get_all_possible_moves()
                ttt_board_ai.update_q_value(state, ai_move, 0, next_state, next_action)
                ttt_board.cycle_turns()
                embed = discord.Embed(title=f"{player_o} | {player_x}\nCurrent Turn: {ttt_board.get_current_turns()}", description=ttt_board.get_board_string())
                await message.edit(embed=embed)
        except InvalidMoveError:
            await message.edit(content="Player has won after AI made an invalid move!", view=None)
            delete_player_session(message)

    @app_commands.command()
    @app_commands.checks.has_permissions(administrator=True)
    async def tttb_q_train(self, interaction: discord.Interaction, iteration: int):
        await interaction.response.defer()
        winner_plot_list = []
        win_counter = 0
        lose_plot_list = []
        lose_counter = 0
        draw_plot_list = []
        draw_counter = 0
        iter_list = []
        for i in range(iteration):
            print(i)
            trainer = random.choice(["O", "X"])
            board = await asyncio.to_thread(lambda: Board("Player1", "Player2"))
            board_ai = await asyncio.to_thread(lambda: Board_AI(board, trainer))
            while True:
                state = str(board.board)
                all_moves = board.get_all_possible_moves()

                if trainer == board.get_current_turns():
                    action = board_ai.choose_action(state)
                else:
                    action = random.choice(all_moves)

                board.make_move(action)
                next_state = str(board.board)
                winner_symbol = board.check_winning_position()

                reward = 0
                if winner_symbol == trainer:
                    print("Trainer Won")
                    win_counter += 1
                    reward = board.max_turns - board.turn_counter
                elif winner_symbol != trainer and winner_symbol != "":
                    print("Trainer Lost")
                    lose_counter += 1
                    reward = board.turn_counter - board.max_turns
                elif board.turn_counter >= board.max_turns:
                    print("DRAW")
                    reward = 0.5
                    draw_counter += 1

                next_action = board.get_all_possible_moves()
                board_ai.update_q_value(state, action, reward, next_state, next_action)

                if winner_symbol != "" or board.turn_counter >= board.max_turns:
                    iter_list.append(i + 1)
                    winner_plot_list.append(win_counter)
                    lose_plot_list.append(lose_counter)
                    draw_plot_list.append(draw_counter)
                    break

                board.cycle_turns()

            save_q_table(board_ai.q_table)

        fig, ax = plt.subplots()
        ax.plot(iter_list, winner_plot_list, label="Win", color="green")
        ax.plot(iter_list, lose_plot_list, label="Lose", color="red")
        ax.plot(iter_list, draw_plot_list, label="Draw", color="gray")
        ax.set_xlabel("Iteration Count")
        ax.set_ylabel("Outcome")
        ax.set_xlim(0, iteration)
        ax.set_title(f"Tic-Tac-Toe-Bolt Q-Learning: Training Result on Iteration Range {iteration}")
        ax.legend()
        with io.BytesIO() as image_binary:
            fig.savefig(image_binary, format="png")
            image_binary.seek(0)
            await interaction.followup.send("Tic-Tac-Toe-Bolt Training Complete", file=discord.File(image_binary, filename="tttb-q-learning-output.png"))

async def setup(bot: commands.Bot):
    await bot.add_cog(TicTaeToeBolt(bot))